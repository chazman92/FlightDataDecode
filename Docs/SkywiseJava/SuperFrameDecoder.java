package foundry.decoder.logic;

import foundry.decoder.raw.Frame;
import foundry.decoder.writers.DARSampleConverter;
import org.apache.spark.sql.Row;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * Takes a superframe and decodes each line, converting according to the given converter.
 * Rows are kept in an array list (assumption is individual SuperFrames aren't too long)
 * and can be iterated over by the caller.
 */
public class SuperFrameDecoder {
    private static final Logger log = LoggerFactory.getLogger(SuperFrameDecoder.class);

    private final DARSampleConverter converter;
    private final Decoder decoder;

    public SuperFrameDecoder(Decoder decoder, DARSampleConverter converter) {
        this.converter = converter;
        this.decoder = decoder;
    }

    public List<Row> decode(Frame[] superFrame) {
        List<Row> output = new ArrayList<>();

        for (int sfc = 0; sfc < superFrame.length; ++sfc) {
            if (superFrame[sfc] == null) {
                // Sync behaviour is currently to set timestamp to first non-null frame, to balance not incrementing here
                // But unclear if correct when using tag files
                continue;
            }

            for (int subFrameIdx = 0; subFrameIdx < 4; ++subFrameIdx) {

                output.addAll(decoder.decodeFrame(superFrame, sfc, subFrameIdx));

                // TODO if we always apply resynchronisation
                // This method should only return values and offset in superframe
                // And converter should apply later
                converter.incrementCurrentTimestamp();
            }
        }

        return output;
    }

}
