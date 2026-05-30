package com.example.legacymock.controller;

import com.example.legacymock.dto.ErpOrderResponse;
import com.example.legacymock.service.ErpLegacyService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/legacy/erp")
public class ErpLegacyController {
    private final ErpLegacyService service;

    public ErpLegacyController(ErpLegacyService service) {
        this.service = service;
    }

    @GetMapping("/orders/{orderId}")
    public ErpOrderResponse getOrder(@PathVariable String orderId) {
        return service.getOrder(orderId);
    }
}
