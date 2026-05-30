package com.example.legacymock.service;

import com.example.legacymock.connector.MockPdmConnector;
import com.example.legacymock.dto.PdmPartResponse;
import org.springframework.stereotype.Service;

@Service
public class PdmLegacyService {
    private final MockPdmConnector connector;

    public PdmLegacyService(MockPdmConnector connector) {
        this.connector = connector;
    }

    public PdmPartResponse getPart(String partId) {
        return connector.findById(partId)
                .orElseThrow(() -> new LegacyResourceNotFoundException("PDM part not found: " + partId));
    }
}
