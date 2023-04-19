package foundry.decoder.logic;

import com.google.common.base.Optional;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.Maps;
import com.google.common.io.ByteStreams;
import com.google.common.io.CountingInputStream;
import foundry.decoder.Utils;
import foundry.decoder.dataframe.Parameter;
import foundry.decoder.dataframe.RecordingSampleAndParameter;
import foundry.decoder.input.DecodingSettings;
import foundry.decoder.input.TimestampParameter;
import foundry.decoder.raw.AlignedPaddedStream;
import foundry.decoder.raw.DARSamples;
import foundry.decoder.raw.Envelope;
import foundry.decoder.raw.Frame;
import foundry.decoder.raw.TagInterval;
import foundry.decoder.writers.DARSampleConverter;
import org.apache.spark.sql.Row;
import org.jooq.tools.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import scala.Tuple2;

import java.io.IOException;
import java.io.InputStream;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Function;
import java.util.stream.Collectors;


/**
 * This class contains the core decoding logic
 */
public class RawDecoder {

    private static final Logger log = LoggerFactory.getLogger(RawDecoder.class);

    public static Iterator<Row> decode(DecodingSettings settings, Envelope envelope) throws IOException {

        DARSampleConverter converter = new DARSampleConverter(settings, envelope);

        DARSamples samples = DARSamples.fromEnvelope(envelope.dataFrame());
        Decoder decoder = new Decoder(samples, converter, envelope.dataFrame().globalConfiguration().subFrameWordCount());
        SuperFrameDecoder superFrameDecoder = new SuperFrameDecoder(decoder, converter);

        List<TagInterval> intervals = envelope.tagIntervals();
 
        InputStream datStream = envelope.datStream();
        if (settings.alignAndPadRequired()) {
            log.info("Aligning and padding the input stream");
            datStream = new AlignedPaddedStream(envelope.datStream(), envelope.syncWords(),
                    envelope.dataFrame().globalConfiguration().subFrameWordCount(), envelope.byteOrder());
        }
        // Not sure if end bound is exclusive or not, reading one extra byte won't read an extra frame
        long endOffset = envelope.datOffset().end() == Long.MAX_VALUE ? Long.MAX_VALUE : envelope.datOffset().end() + 1;
        CountingInputStream cis = new CountingInputStream(ByteStreams.limit(datStream, endOffset));

        ByteStreams.skipFully(cis, envelope.datOffset().start());

        AtomicBoolean synchronised = new AtomicBoolean(false);
        boolean isCheckDesync = settings.checkDesync();
        boolean isSyncTimeAlways = settings.syncTimeAlways();

        return new ExceptionWrappingIterator<>(
                FluentIterable.from(intervals)
                        .transformAndConcat(interval -> () -> {
                            // If we're using tags and timestamp params, ensure we resync time each interval
                            synchronised.set(false);
                            return new IntervalReader(interval, converter, cis, envelope);
                        })
                        // .peek(x -> log.info("Decoded an interval"))
                        .transform(currentAndNextSuperframe -> maybeSynchronise(currentAndNextSuperframe,
                                synchronised, converter, envelope, settings.maxDayDifference(), isCheckDesync, isSyncTimeAlways))
                        .transform(superframe -> checkDesync(superframe, synchronised))
                        .transformAndConcat(superFrame -> superFrameDecoder.decode(superFrame))
                        .iterator(),
                settings, envelope);
    }

    private static Frame[] maybeSynchronise(Tuple2<Frame[], Frame[]> currentAndNextSuperframe, AtomicBoolean
            synchronised, DARSampleConverter converter, Envelope envelope, Integer maxDayDifference, boolean isCheckDesync, boolean isSyncTimeAlways) {

        // As we iterate over the frames, check for desynchronisation and resync the time if this occurs
        // This is a null-op if the time parameters aren't specified
        // We resync on this superframe if we desynced on the previous one (or it's start), so need to pass flag through
        // Since a superframe may be partially filled, we decode the valid frames, then sync next time
        // A desync occurs if there was a frame skip or we lost the sync words

        if ((envelope.timestampParameters().isPresent() && !synchronised.get()) || isSyncTimeAlways) {
            Optional<Long> syncTime = syncTime(currentAndNextSuperframe._1, currentAndNextSuperframe._2, envelope, maxDayDifference);
            if (syncTime.isPresent() && registrationInSync(currentAndNextSuperframe._1, envelope)) {
                converter.setCurrentTimestamp(syncTime.get());
                synchronised.set(true);
            } else if(isCheckDesync) {
                // If we failed to synchronise ():
                //     - if 'isCheckDesync = true' null out this superframe so we don't decode anything of this superframe
                //     - otherwise, keep the decoded data of this superframe
                // Will reattempt synchronisation next time
				Arrays.fill(currentAndNextSuperframe._1, null);
            }
        }


        // Return current superframe for chaining
        return currentAndNextSuperframe._1;
    }

    private static Frame[] checkDesync(Frame[] superFrame, AtomicBoolean synchronised) {
        // Start of superframe can be null if its first in interval
        if (superFrame[superFrame.length - 1] == null) {
            // Frame counter skip or word desync
            synchronised.set(false);
        }
        // Return for chaining
        return superFrame;
    }

    private static boolean registrationInSync(Frame[] superframe, Envelope envelope) {

        Optional<List<String>> registrationParameters = envelope.registrationParameters();

        if (!registrationParameters.isPresent())
            return true;

        Map<String, Parameter> allParameters =
                envelope.dataFrame().parameters().stream().collect(Collectors.toMap(Parameter::mnemonic, Function.identity()));

        String registration = registrationParameters.get().stream()
                .map(param -> getFirstValue(superframe, allParameters.get(param)))
                .collect(Collectors.joining());

        registration = registration.replaceAll("[^A-Za-z]+", "").toUpperCase();
        String expectedRegistration = envelope.tailNumber().replaceAll("[^A-Za-z]+", "").toUpperCase();

        log.info("Syncing registration. Expected: {}, Actual: {}", expectedRegistration, registration);
        return registration.equals(expectedRegistration);
    }

    private static Optional<Long> syncTime(Frame[] currentSuperframe, Frame[] nextSuperFrame, Envelope envelope, Integer maxDayDifference) {
        log.info("Synchronising time");

        Optional<Long> filenameTimeMillis = envelope.fileNameTimeOffset().transform(Duration::toMillis);
        int fileNameYear =
                filenameTimeMillis.transform(millis -> Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).getYear())
                        .or(2000); // Just debugging, use 2000

        // Check current and next superframe for better reliability
        // Also means we'll need at least 2 superframes of data (probably a good thing, avoid weird tiny intervals)
        Optional<Long> syncTime = tryFetchTime(envelope.timestampParameters().get(),
                envelope.dataFrame().parameters(), currentSuperframe, fileNameYear);
        Optional<Long> nextTime = tryFetchTime(envelope.timestampParameters().get(),
                envelope.dataFrame().parameters(), nextSuperFrame, fileNameYear);

        if (!(syncTime.isPresent() && nextTime.isPresent())) {
            envelope.eventLogger().error(envelope.darUuid(), "Time in current superframe or next superframe don't exist");
            return Optional.absent();
        }

        LocalDateTime currentSuperFrameTime = Instant.ofEpochMilli(syncTime.get()).atZone(ZoneOffset.UTC).toLocalDateTime();
        LocalDateTime now = ZonedDateTime.now(ZoneOffset.UTC).toLocalDateTime();
        Duration diff = Duration.between(now, currentSuperFrameTime);
        if (diff.getSeconds() >= 1) {
          envelope.eventLogger().error(envelope.darUuid(), "Ignore decode this file, because filename timestamp come from future, current superframe time = " + currentSuperFrameTime + ", now = " + now);
          return Optional.absent();
        }

        // If two superframes are too far apart, something is wrong
        // A superframe should be 64 seconds of data
        if (nextTime.get() - syncTime.get() > Duration.ofSeconds(70).toMillis()) {
            envelope.eventLogger().error(envelope.darUuid(), "Time in current superframe and next superframe are not reliability, it exceed seconds of superframe, span time between current and next superframe = " + (nextTime.get() - syncTime.get()) + " (UTC milliseconds)");
            return Optional.absent();
        }

        // Filter out times that are too far away from file name time, likely they are invalid
        if ((filenameTimeMillis.isPresent() && Math.abs(syncTime.get() - filenameTimeMillis.get()) > Duration.ofDays(maxDayDifference).toMillis())) {
            envelope.eventLogger().error(envelope.darUuid(), "Time in current superframe was too far away from filename timestamp, span time between current superframe and filename timestamp = " + (syncTime.get() - filenameTimeMillis.get()) + " (UTC milliseconds)");
            return Optional.absent();
        }
        
        log.info("Synced time: {}", syncTime.get());

        return syncTime;
    }

    private static Optional<Long> tryFetchTime(Map<String, TimestampParameter> timestampParameters,
                                               List<Parameter> allParameters, Frame[] superframe,
                                               int filenameYear) {

        // First frame might not be index 0
        Frame[] frames = Arrays.stream(superframe).filter(Objects::nonNull).toArray(Frame[]::new);
        Map<String, Parameter> parameterMap = allParameters.stream()
                .collect(Collectors.toMap(Parameter::mnemonic, Function.identity()));
        Map<String, Tuple2<Parameter, TimestampParameter>> timeParameters = Maps.transformValues(timestampParameters,
                param -> new Tuple2<>(parameterMap.get(param.mnemonic()), param));

        List<String> missingParams =
                timeParameters.values().stream().filter(v -> v._1 == null)
                        .map(v -> v._2.mnemonic()).collect(Collectors.toList());
        if (!missingParams.isEmpty()) {
            throw new FailAlwaysException("Timestamp parameters " + missingParams + " don't exist in dataframe");
        }

        try {

            // Compare consecutive timestamps until only the second is changing
            // This should take at most 2 comparisons
            // This avoids problems caused by readings of different time components in different subframes not aligning
            for (int i = 1; i < frames.length; ++i) {
                ZonedDateTime time1 = getTime(frames, i - 1, timeParameters, filenameYear);
                ZonedDateTime time2 = getTime(frames, i, timeParameters, filenameYear);

                if (time1.truncatedTo(ChronoUnit.MINUTES).equals(time2.truncatedTo(ChronoUnit.MINUTES))) {

                    Parameter second = timeParameters.get("second")._1;

                    RecordingSampleAndParameter sample =
                            RecordingSampleAndParameter.of(second.parameterRecordingConfiguration().samples().get(0), second);
                    int subframeId = sample.highestRatePart().location().subFrames().stream().sorted().findFirst()
                            .get();

                    // Adjust to first non-null frame in superframe, and then adjust for subframe seconds was from
                    // Currently when skipping null frames we don't increment the timestamp
                    // So we want to set the timestamp to be the first non-null frame in the superframe
                    // Which is what i is, since we filtered out nulls
                    ZonedDateTime syncTime = time1.minusSeconds((i - 1) * 4).minusSeconds(subframeId - 1);
                    log.info("Synced one superframe time: {}", syncTime);

                    return Optional.of(syncTime.toEpochSecond() * 1000);
                }
            }
        } catch (Exception e) {
            log.warn("Error synchronising {}", e);
        }

        // Insufficient frames in this superframe or seconds never aligned (or error)
        log.warn("Time synchronisation failed. Superframe had {} non-null frames.", frames.length);
        return Optional.absent();
    }


    private static ZonedDateTime getTime(Frame[] superframe, int frameIdx,
                                         Map<String, Tuple2<Parameter, TimestampParameter>> timeParameters,
                                         int fileNameYear) {
        int second = getFirstValue(superframe, timeParameters.get("second"), frameIdx);
        int minute = getFirstValue(superframe, timeParameters.get("minute"), frameIdx);
        int hour = getFirstValue(superframe, timeParameters.get("hour"), frameIdx);
        // Sometimes there is no year parameter
        int year = timeParameters.containsKey("year") ?
                getFirstValue(superframe, timeParameters.get("year"), frameIdx) : fileNameYear;
        year = year > 100 ? year : year + 2000;

        if (timeParameters.containsKey("dayOfYear")) {
            int dayOfYear = getFirstValue(superframe, timeParameters.get("dayOfYear"), frameIdx);
            ZonedDateTime time = ZonedDateTime.of(year, 1, 1, hour, minute, second, 0, ZoneOffset.UTC);
            return time.withDayOfYear(dayOfYear);
        } else {
     
     
            int day = getFirstValue(superframe, timeParameters.get("day"), frameIdx);
            int month = getFirstValue(superframe, timeParameters.get("month"), frameIdx);
            return ZonedDateTime.of(year, month, day, hour, minute, second, 0, ZoneOffset.UTC);
        }


    }

    private static String getFirstValue(Frame[] superframe, Parameter parameter) {
        // Get the first value in the frame
        RecordingSampleAndParameter sample =
                RecordingSampleAndParameter.of(
                        parameter.parameterRecordingConfiguration()
                                .samples()
                                .get(0),
                        parameter);

        int subframeId = sample.highestRatePart().location().subFrames().stream().sorted().findFirst().get();
        return (String) Decoder.decodeValue(superframe, 0, subframeId, sample);
    }

    private static int getFirstValue(Frame[] superframe, Tuple2<Parameter, TimestampParameter> parameter, int frameIdx) {
        // Get the first value in the frame
        RecordingSampleAndParameter sample =
                RecordingSampleAndParameter.of(
                        parameter._1.parameterRecordingConfiguration()
                                .samples()
                                .get(0),
                        parameter._1);

        int subframeId = sample.highestRatePart().location().subFrames().stream().sorted().findFirst().get();
        long parameterValue = ((Number) Decoder.decodeValue(superframe, frameIdx, subframeId, sample)).longValue();
        return extractValue(parameterValue, parameter._2, parameter._1);

    }

    private static int extractValue(long value, TimestampParameter extractionDetails, Parameter param) {
        // Sometimes time values are combined into one parameter, e.g. minutes and seconds in the same param

        if (!extractionDetails.lsb().isPresent() || !extractionDetails.length().isPresent()) {
            return (int) value;
        }

        int length = param.parameterRecordingConfiguration().samples().get(0).numBits();
        // MSB first
        String s = StringUtils.leftPad(Long.toBinaryString(value), length, '0');

        int endIdx = s.length() - extractionDetails.lsb().get() + 1;
        int startIdx = endIdx - extractionDetails.length().get();
        String part = s.substring(startIdx, endIdx);
        return Integer.parseUnsignedInt(part, 2);
    }

}

