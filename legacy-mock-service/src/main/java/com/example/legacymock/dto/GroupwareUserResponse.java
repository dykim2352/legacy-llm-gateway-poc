package com.example.legacymock.dto;

import java.util.List;

public record GroupwareUserResponse(
        String userId,
        String username,
        String department,
        String position,
        String email,
        List<String> roles,
        List<String> approvalLine
) {
}
