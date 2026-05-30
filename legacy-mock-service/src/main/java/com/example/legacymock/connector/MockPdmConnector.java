package com.example.legacymock.connector;

import com.example.legacymock.dto.PdmPartResponse;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Component;

@Component
public class MockPdmConnector implements LegacyConnector<String, PdmPartResponse> {
    private final Map<String, PdmPartResponse> parts = Map.of(
            "PART-2001", new PdmPartResponse(
                    "PART-2001",
                    "Secure Gateway Board",
                    "R3",
                    "RELEASED",
                    "AI Platform Team",
                    List.of("R1: Initial design", "R2: Thermal improvement", "R3: Security chip updated"),
                    List.of("DOC-SAMPLE-001", "DOC-SAMPLE-002")
            ),
            "PART-2002", new PdmPartResponse(
                    "PART-2002",
                    "Mock Signal Adapter",
                    "R1",
                    "IN_REVIEW",
                    "Integration Team",
                    List.of("R1: Prototype review"),
                    List.of("DOC-SAMPLE-003")
            )
    );

    @Override
    public Optional<PdmPartResponse> findById(String id) {
        return Optional.ofNullable(parts.get(id));
    }
}
