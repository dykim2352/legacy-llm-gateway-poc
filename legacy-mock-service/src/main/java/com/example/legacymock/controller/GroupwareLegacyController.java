package com.example.legacymock.controller;

import com.example.legacymock.dto.GroupwareUserResponse;
import com.example.legacymock.service.GroupwareLegacyService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/legacy/groupware")
public class GroupwareLegacyController {
    private final GroupwareLegacyService service;

    public GroupwareLegacyController(GroupwareLegacyService service) {
        this.service = service;
    }

    @GetMapping("/users/{userId}")
    public GroupwareUserResponse getUser(@PathVariable String userId) {
        return service.getUser(userId);
    }
}
