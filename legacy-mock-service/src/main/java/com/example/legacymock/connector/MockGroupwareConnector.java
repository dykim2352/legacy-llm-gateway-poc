package com.example.legacymock.connector;

import com.example.legacymock.dto.GroupwareUserResponse;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Component;

@Component
public class MockGroupwareConnector implements LegacyConnector<String, GroupwareUserResponse> {
    private final Map<String, GroupwareUserResponse> users = Map.of(
            "USER-3001", new GroupwareUserResponse(
                    "USER-3001",
                    "Kim Engineer",
                    "AI Platform Team",
                    "Senior Engineer",
                    "kim.engineer@example.invalid",
                    List.of("USER", "APPROVER"),
                    List.of("Team Reviewer", "Platform Approver")
            ),
            "USER-3002", new GroupwareUserResponse(
                    "USER-3002",
                    "Lee Reviewer",
                    "Integration Team",
                    "Reviewer",
                    "lee.reviewer@example.invalid",
                    List.of("USER", "REVIEWER"),
                    List.of("Integration Reviewer", "Operations Approver")
            )
    );

    @Override
    public Optional<GroupwareUserResponse> findById(String id) {
        return Optional.ofNullable(users.get(id));
    }
}
