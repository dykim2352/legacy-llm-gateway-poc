package com.example.legacymock.controller;

import com.example.legacymock.dto.PdmPartResponse;
import com.example.legacymock.service.PdmLegacyService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/legacy/pdm")
public class PdmLegacyController {
    private final PdmLegacyService service;

    public PdmLegacyController(PdmLegacyService service) {
        this.service = service;
    }

    @GetMapping("/parts/{partId}")
    public PdmPartResponse getPart(@PathVariable String partId) {
        return service.getPart(partId);
    }
}
