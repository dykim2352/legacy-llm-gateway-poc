package com.example.legacymock.connector;

import com.example.legacymock.dto.ErpOrderResponse;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Component;

@Component
public class MockErpConnector implements LegacyConnector<String, ErpOrderResponse> {
    private final Map<String, ErpOrderResponse> orders = Map.of(
            "ORD-1001", new ErpOrderResponse(
                    "ORD-1001",
                    "Sample Customer Alpha",
                    "ITEM-AX-100",
                    "Tactical Network Module",
                    12,
                    new BigDecimal("1250.00"),
                    "USD",
                    "IN_PROGRESS",
                    LocalDate.of(2026, 5, 20),
                    LocalDate.of(2026, 6, 30)
            ),
            "ORD-1002", new ErpOrderResponse(
                    "ORD-1002",
                    "Sample Customer Beta",
                    "ITEM-BR-200",
                    "Field Relay Unit",
                    5,
                    new BigDecimal("980.00"),
                    "USD",
                    "WAITING_FOR_PART",
                    LocalDate.of(2026, 5, 22),
                    LocalDate.of(2026, 7, 10)
            )
    );

    @Override
    public Optional<ErpOrderResponse> findById(String id) {
        return Optional.ofNullable(orders.get(id));
    }
}
