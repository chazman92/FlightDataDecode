package foundry.decoder.logic;

import com.google.common.io.ByteStreams;
import com.google.common.io.CountingInputStream;
import foundry.decoder.dataframe.GlobalConfiguration;
import foundry.decoder.raw.Envelope;
import foundry.decoder.raw.Frame;
import foundry.decoder.raw.FrameReader;
import foundry.decoder.raw.Tag;
import foundry.decoder.raw.TagInterval;
import foundry.decoder.writers.DARSampleConverter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import scala.Tuple2;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.time.Duration;
import java.util.Iterator;
import java.util.Optional;

/**
 * Handles reading of a single tag interval.
 */
public class IntervalReader implements Iterator<Tuple2<Frame[], Frame[]>> {
    private static final Logger log = LoggerFactory.getLogger(IntervalReader.class);

    private static final int FRAME_COUNT_MODULO = 1 << 12;

    private final Envelope envelope;
    private final FrameReader frameReader;

    private boolean hasNext;
    private Frame[] nextSuperFrame;

    private int lastReadFrameCounter = -1;

    public IntervalReader(TagInterval interval, DARSampleConverter converter,
                          CountingInputStream cis, Envelope envelope) {
        Tag startTag = interval.start();
        Tag endTag = interval.end();
        this.envelope = envelope;

        log.info("Decoding interval: {} - {}", startTag.getTimestamp(), endTag.getTimestamp());


        // If tags are present, use them as timestamp, otherwise use filename timestamp
        // Default tag interval when no tags will have -1 seconds as timestamp
        // If timestamp parameters are present, they will always override this timestamp later
        Optional<Long> maybeTagTimestamp = startTag.getTimestamp().getMillis() == -1000 ? Optional.empty() :
                Optional.of(startTag.getTimestamp().getMillis());
        converter.setCurrentTimestamp(maybeTagTimestamp.orElse(envelope.fileNameTimeOffset().or(Duration.ZERO).toMillis()));

        int bytesToSkip = startTag.getOffsetInData() - (int) cis.getCount();

        log.info("Skipping {} bytes", bytesToSkip);

        try {
            ByteStreams.skipFully(cis, bytesToSkip);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        long limit = endTag.getOffsetInData() - startTag.getOffsetInData();

        if (limit < 0) {
            throw new RuntimeException("Interval has invalid range");
        }

        InputStream lis = ByteStreams.limit(cis, limit);

        frameReader = new FrameReader(lis, envelope.byteOrder(),
                envelope.dataFrame().globalConfiguration().subFrameWordCount());

        nextSuperFrame = readNextSuperFrame();
    }

    private Frame[] readNextSuperFrame() {

        // This method is called before iterator.next() (and hasNext) is called, since one superframe is cached
        // Hence we should check if there is anything left to read here, since if we checked in hasNext
        // then the superframe would already have been read and cached, and there might be no more words
        hasNext = frameReader.hasMoreWords();

        // Returns null frames on a frame counter skip or word desync
        // We should resync time base in this case
        // If we aren't performing resyncing, then a frame being pushed to the next superframe
        // should affect deocding/timestamps

        int framesInSuperFrame = envelope.dataFrame().globalConfiguration().framesInSuperFrame();
        Frame[] nextSuperFrame = new Frame[framesInSuperFrame];


        int lastReadSuperFrameIdx = -1;
        Optional<Frame> frame = attemptReadNextFrame();


        // Check that the next frame has a count 1 greater
        // And stop once we cycle through to a new superframe
        while (frame.isPresent()
                && (lastReadFrameCounter == -1
                // Check frame is strictly next
                || Math.floorMod(frame.get().getDfc() - lastReadFrameCounter, FRAME_COUNT_MODULO) == 1)
                // Check we haven't started a new superframe
                && frame.get().getSfc() > lastReadSuperFrameIdx) {
            nextSuperFrame[frame.get().getSfc()] = frame.get();
            lastReadSuperFrameIdx = frame.get().getSfc();
            lastReadFrameCounter = frame.get().getDfc();
            frame = attemptReadNextFrame();
        }

        // TODO What if counter decreases?
        // what if it increased a lot (incorrectly), and then we skip all subsequent frames

        if (frame.isPresent()) {
            // Counter skip (or reached end of superframe), unread for next time
            frameReader.unreadFrame();
        }

        // Start of superframe might be null if its first
        if (nextSuperFrame[framesInSuperFrame - 1] == null) {
            // Desync, reset the frame counter
            lastReadFrameCounter = -1;
        }

        return nextSuperFrame;

    }

    // Empty optional if desync or EOF
    // Complete frame otherwise
    //
    private Optional<Frame> attemptReadNextFrame() {
        try {
            GlobalConfiguration gc = envelope.dataFrame().globalConfiguration();
            return frameReader.readNextFrame(envelope.dataFrame().globalConfiguration().subFrameWordCount(), envelope.syncWords())
                    .map(subFrames -> new Frame(subFrames, gc.subFrameCounterLocation(), gc.dataFrameCounterLocation()));
        } catch (EOFException e) {
            return Optional.empty();
        }
    }

    @Override
    public boolean hasNext() {
        return hasNext;
    }

    @Override
    public Tuple2<Frame[], Frame[]> next() {
        // Return 2 superframes at a time, for better synchronisation
        Frame[] current = nextSuperFrame;
        nextSuperFrame = readNextSuperFrame();
        return new Tuple2<>(current, nextSuperFrame);
    }

    public void resetFrameCounter() {
        lastReadFrameCounter = -1;
    }
}
