package at.ac.univie.fog.repository;

import at.ac.univie.fog.data.AggregatedData;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface FogRepository extends JpaRepository<AggregatedData, Long> {
}
