package com.example.legacymock.service;

import com.example.legacymock.connector.MockErpConnector;
import com.example.legacymock.dto.ErpOrderResponse;
import org.springframework.stereotype.Service;

@Service
public class ErpLegacyService {
    private final MockErpConnector connector;

    public ErpLegacyService(MockErpConnector connector) {
        this.connector = connector;
    }

    public ErpOrderResponse getOrder(String orderId) {
        return connector.findById(orderId)
                .orElseThrow(() -> new LegacyResourceNotFoundException("ERP order not found: " + orderId));
    }
}
