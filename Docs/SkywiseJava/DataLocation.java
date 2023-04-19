package foundry.decoder.dataframe;

import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.google.common.base.Preconditions;
import org.immutables.value.Value;

import javax.annotation.Nonnull;
import java.io.Serializable;
import java.util.Arrays;
import java.util.List;

import static java.util.stream.Collectors.toList;

/** A parameter (or dataframe/subframe counter) location within one (or more) subframes. */
@Value.Immutable
@JsonDeserialize(as = ImmutableDataLocation.class)
public interface DataLocation extends Comparable<DataLocation>, Serializable {

    int word();

    /** Aka the least significant bit. */
    int firstBitInWord();

    int lengthInBits();

    List<String> unParsedSubFrames();

    @Value.Derived
    default List<Integer> subFrames() {
        if (unParsedSubFrames().size() == 1 && unParsedSubFrames().get(0).equals("ALL")) {
            return Arrays.asList(1, 2, 3, 4);
        } else {
            return unParsedSubFrames().stream().map(Integer::parseInt).collect(toList());
        }
    }

    /** How often this data is recorded per second (dependent on how many subframes it appears in a frame) */
    @Value.Derived
    default float frequency() {
        // One subframe is a second, and there are 4 subframes per frame hence frequency is #subframes / 4
        return subFrames().size() / 4f;
    }


    /** Get the relative time offset from the start of the sub-frame for this location. */
    default long timeOffset(int numWordsInSubFrame) {
        return ((word() * 1000) / numWordsInSubFrame);
    }

    /**
     * Compare DataLocations by checking which frame the parameter occurs in.
     *
     * @param o location to compare to
     * @return value to be used for comparisons
     */
    @Override
    default int compareTo(@Nonnull DataLocation o) {
        if (this.subFrames().size() != o.subFrames().size()) {
            // If the other location occurs more often, its greater
            return o.subFrames().size() - this.subFrames().size();
        } else {
            if (this.subFrames().size() == 4) {
                // If both occur equally often (i.e. every subframe)
                return 0;
            } else {
                // TODO this whole method
                // If other location occurs later on in subframes, its greater ????
                // i.e. 3,4 is greater than 2,3
                // Are these even sorted?
                // * This comparison is flipped, ie its o - this not this - a
                // So if other is has bigger first frame, its smaller
                // Note that minimum is taken, so this behaviour makes sense
                // I.e. highest rate is later occurring one which means when its sampled
                // other parts will have a value
                return o.subFrames().get(0) - this.subFrames().get(0);
            }
        }
    }

    /** The only sub-frame this parameter occurs in. Throws an exception if there is more than one */
    default int getSingleSubFrameNumber() throws IllegalStateException {
        Preconditions.checkState(subFrames().size() == 1, "This location represents multiple subframes");
        return subFrames().get(0);
    }

    /** Check if this location occurs in a specific subframe */
    default boolean occursInSubFrame(int subFrame) {
        return subFrames().contains(subFrame);
    }

    /**
     * Given the current sub-frame which sub-frame should be used to read data from.
     *
     * @param subFrameBeingRead current sub-frame
     * @return sub-frame to read from
     */
    default int getSubFrameToReadFrom(int subFrameBeingRead) {

        // TODO
        // contract of binary search works here, as if it doesn't find element it returns one before it
        // Arrays.binarySearch()

        // What happens if there is no subframe before the one being read?

        if (subFrames().size() == 1) {
            return subFrames().get(0);
        } else {
            if (!subFrames().contains(subFrameBeingRead)) {
                int subFrameIdBeforeSubFrameBeingRead = 0;
                for (int frame : subFrames()) {
                    if (subFrameBeingRead >= frame && frame > subFrameIdBeforeSubFrameBeingRead) {
                        subFrameIdBeforeSubFrameBeingRead = frame;
                    }
                }
                return subFrameIdBeforeSubFrameBeingRead;
            } else {
                return subFrameBeingRead;
            }
        }
    }

}
