package com.example.legacymock.service;

import com.example.legacymock.connector.MockGroupwareConnector;
import com.example.legacymock.dto.GroupwareUserResponse;
import org.springframework.stereotype.Service;

@Service
public class GroupwareLegacyService {
    private final MockGroupwareConnector connector;

    public GroupwareLegacyService(MockGroupwareConnector connector) {
        this.connector = connector;
    }

    public GroupwareUserResponse getUser(String userId) {
        return connector.findById(userId)
                .orElseThrow(() -> new LegacyResourceNotFoundException("Groupware user not found: " + userId));
    }
}
