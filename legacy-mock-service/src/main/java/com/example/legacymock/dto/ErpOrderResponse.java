package com.example.legacymock.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record ErpOrderResponse(
        String orderId,
        String customerName,
        String itemCode,
        String itemName,
        int quantity,
        BigDecimal unitPrice,
        String currency,
        String orderStatus,
        LocalDate requestedAt,
        LocalDate deliveryDueDate
) {
}
