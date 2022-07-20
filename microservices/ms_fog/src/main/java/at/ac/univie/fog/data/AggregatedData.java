package at.ac.univie.fog.data;

import javax.persistence.*;
import java.time.LocalDate;

/**
 * Aggregated sensor data sent to MS ML.
 */
@Entity
@Table(name = "aggregated_data")
@lombok.Data
@lombok.NoArgsConstructor
public class AggregatedData {

    @Id
    @GeneratedValue(strategy= GenerationType.AUTO)
    @Column(name = "ID")
    private Long id;

    @Column(name = "dataType")
    private String dataType;

    @Column(name = "aggregationMode")
    private String aggregationMode;

    @Column(name = "aggregationInterval")
    private String aggregationInterval;

    @Column(name = "timestamp")
    private LocalDate timestamp;

    @Column(name = "dataValue")
    private double dataValue;

    public AggregatedData(ESensor dataType, EAggregationMode aggregationMode, EAggregationInterval aggregationInterval, LocalDate timestamp, double dataValue) {
        this.dataType = dataType.toString();
        this.aggregationMode = aggregationMode.toString();
        this.aggregationInterval = aggregationInterval.toString();
        this.timestamp = timestamp;
        this.dataValue = dataValue;
    }

    @Override
    public String toString() {
        return "AggregatedData(" +
                "dataType='" + dataType + '\'' +
                ", aggregationMode='" + aggregationMode + '\'' +
                ", aggregationInterval='" + aggregationInterval + '\'' +
                ", timestamp=" + timestamp +
                ", dataValue=" + dataValue +
                ')';
    }

}
