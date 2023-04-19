package foundry.decoder.logic;

import com.google.common.collect.ImmutableMap;
import foundry.decoder.binary_parsers.BCDValueParser;
import foundry.decoder.binary_parsers.BNRValueParser;
import foundry.decoder.binary_parsers.BinGmtParser;
import foundry.decoder.binary_parsers.ISO5ValueParser;
import foundry.decoder.binary_parsers.PartValuesDecoder;
import foundry.decoder.binary_parsers.UnknownFormatValueParser;
import foundry.decoder.dataframe.DataLocation;
import foundry.decoder.dataframe.ParameterRecordingPart;
import foundry.decoder.dataframe.RecordingSampleAndParameter;
import foundry.decoder.raw.DARSamples;
import foundry.decoder.raw.Frame;
import foundry.decoder.writers.DARSampleConverter;
import org.apache.commons.lang.ArrayUtils;
import org.apache.spark.sql.Row;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class Decoder {

    private static final Logger log = LoggerFactory.getLogger(Decoder.class);

    private final DARSamples samples;
    private final DARSampleConverter converter;
    private final int numWordsInSubFrame;

    /**
     * These are per value binary_parsers. Each value maybe encoded differently i.e. strings are
     * encoded as ISO#5 and some numerical values are BNR. Which decoder to use is configured in
     * the dataframe
     */
    private static final Map<String, PartValuesDecoder> DECODERS_BY_FORMAT = ImmutableMap.<String, PartValuesDecoder>builder()
            .put("BNR", new BNRValueParser())
            .put("INT", new BNRValueParser())
            .put("DIS", new BNRValueParser())
            .put("ISO#5", new ISO5ValueParser())
            .put("ASCII", new ISO5ValueParser())
            .put("BCD", new BCDValueParser())
            .put("BINGMT", new BinGmtParser())
    .build();

    private static final PartValuesDecoder unknownFormatDecoder = new UnknownFormatValueParser();

    public Decoder(DARSamples samples, DARSampleConverter converter, int numWordsInSubFrame) {
        this.samples = samples;
        this.converter = converter;
        this.numWordsInSubFrame = numWordsInSubFrame;
    }


    public List<Row> decodeFrame(Frame[] superFrame, int superframeIdx, int subframeIdx) {

        List<Row> values = new ArrayList<>();

        for (RecordingSampleAndParameter sample : samples.getFrameSamples(superframeIdx, subframeIdx)) {
            //TODO clean this try/catch
            try {
                Object decodedValue = Decoder.decodeValue(superFrame, superframeIdx, subframeIdx + 1, sample);
                if (decodedValue != null) {
                    Row output = converter.convert(sample, decodedValue, numWordsInSubFrame);
                    values.add(output);
                }
            } catch (Exception e) {
            }
        }

        return values;
    }



    public static Object decodeValue(Frame[] superFrame, int frameIdx, int subFrameId, RecordingSampleAndParameter sample) {
        Integer[] partValues = new Integer[sample.sortedParts().size()];
        Arrays.fill(partValues, null);
        for (ParameterRecordingPart locationPartConfiguration : sample
                .sortedParts()) {
            Frame frame;
            // Superframes can have parts across multiple frames
            if (locationPartConfiguration.computationType().equals("SUPERFRAME")) {
                frame = superFrame[locationPartConfiguration.frameNumberOfSuperframe() - 1];
            } else {
                frame = superFrame[frameIdx];
            }

            Integer partValue = null;
            if (frame != null) {
                DataLocation location = locationPartConfiguration.location();
                int subFrameToReadFrom = location.getSubFrameToReadFrom(subFrameId);
                if (subFrameToReadFrom != 0) {
                    partValue = frame.getSubFrame(subFrameToReadFrom).getRawDataAt(location);
                } else {
                    log.error("Parts re-composition issue on: {}", sample.parameter().mnemonic());
                }
            }
            if (locationPartConfiguration.partNumber() - 1 >= partValues.length) {
                String message = String.format("For parameter with mnemonic %s, there are only %d" +
                                " location_parts, " +
                                "but one of the parts has a part_num of %d",
                        sample.parameter().mnemonic(),
                        sample.sortedParts().size(),
                        locationPartConfiguration.partNumber()
                );
                throw new RuntimeException(message);
            }

            partValues[locationPartConfiguration.partNumber() - 1] = partValue;
        }

        if (Arrays.asList(partValues).contains(null)) {
            return null;
        }

        String dataFormat = sample.parameter().parameterRecordingConfiguration().dataFormat();
        PartValuesDecoder valueDecoder = DECODERS_BY_FORMAT.getOrDefault(dataFormat, unknownFormatDecoder);
        return valueDecoder.combineAndDecode(sample.parameter(), ArrayUtils.toPrimitive(partValues));
    }
}
