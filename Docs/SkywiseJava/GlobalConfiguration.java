package foundry.decoder.dataframe;

import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlProperty;
import com.google.common.base.Preconditions;
import org.immutables.value.Value;

import java.io.Serializable;
import java.util.Arrays;


@Value.Immutable
@JsonDeserialize(as = ImmutableGlobalConfiguration.class)
public interface GlobalConfiguration extends Serializable {

    @Value.Check
    default void check() {
        Preconditions.checkState(framesInSuperFrame() == 16, "There should be 16 frames in a superframe");
    }

    /** Name of the data frame */
    @JacksonXmlProperty(localName = "name")
    String name();

    /** QAR or DAR */
    @JacksonXmlProperty(localName = "data_class")
    String dataClass();

    /** Number of frames in a super-frame. This is always 16. */
    @JacksonXmlProperty(localName = "nb_frames_per_subframe") // Name in XML is wrong
    int framesInSuperFrame();

    /** Number of words in a sub-frame */
    @JacksonXmlProperty(localName = "subframe_word_nb")
    int subFrameWordCount();

    /** Data-frame counter location. Data-frame counter includes the sub-frame counter (? can these be different?). */
    @Value.Derived
    default DataLocation dataFrameCounterLocation() {
        return ImmutableDataLocation.builder()
                .unParsedSubFrames(Arrays.asList(String.valueOf(dataFrameCounterSubFrameIdx())))
                .word(dataFrameCounterWord())
                .lengthInBits(dataFrameCounterBitLength())
                .firstBitInWord(dataFrameCounterLsb())
                .build();
    }

    @JacksonXmlProperty(localName = "dfc_loc_frame")
    int dataFrameCounterSubFrameIdx();
    @JacksonXmlProperty(localName = "dfc_loc_word")
    int dataFrameCounterWord();
    @JacksonXmlProperty(localName = "dfc_bit_source_lsb")
    int dataFrameCounterLsb();
    @JacksonXmlProperty(localName = "dfc_bit_length")
    int dataFrameCounterBitLength();

    /** Sub-frame counter location */
    @Value.Derived
    default DataLocation subFrameCounterLocation() {
        return ImmutableDataLocation.builder()
                .unParsedSubFrames(Arrays.asList(String.valueOf(subFrameCounterSubFrameIdx())))
                .word(subFrameCounterWord())
                .lengthInBits(subFrameCounterBitLength())
                .firstBitInWord(subFrameCounterLsb())
                .build();
    }

    @JacksonXmlProperty(localName = "sfc_loc_frame")
    int subFrameCounterSubFrameIdx();
    @JacksonXmlProperty(localName = "sfc_loc_word")
    int subFrameCounterWord();
    @JacksonXmlProperty(localName = "sfc_bit_source_lsb")
    int subFrameCounterLsb();
    @JacksonXmlProperty(localName = "sfc_bit_length")
    int subFrameCounterBitLength();

}
