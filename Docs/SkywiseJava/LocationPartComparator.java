package foundry.decoder.dataframe;

import java.io.Serializable;
import java.util.Comparator;

public class LocationPartComparator implements
        Comparator<ParameterRecordingPart>, Serializable {

    @Override
    public int compare(ParameterRecordingPart o1,
                       ParameterRecordingPart o2) {
        if (o1.computationType().equals("SUPERFRAME")) {
            switch (o2.computationType()) {
                case "SUPERFRAME":
                    if (o1.frameNumberOfSuperframe() < o2.frameNumberOfSuperframe()) {
                        return 1;
                    } else if (o1.frameNumberOfSuperframe() > o2.frameNumberOfSuperframe()) {
                        return -1;
                    } else {
                        return o1.location().compareTo(o2.location());
                    }
                case "REGULAR":
                    return 1;
                default:
                    throw new RuntimeException();
            }
        } else if (o1.computationType().equals("REGULAR")) {
            switch (o2.computationType()) {
                case "SUPERFRAME":
                    return -1;
                case "REGULAR":
                    return o1.location().compareTo(o2.location());
                default:
                    throw new RuntimeException();
            }
        }
        return 0;
    }
}
