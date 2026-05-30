package com.example.legacymock.dto;

import java.util.List;

public record PdmPartResponse(
        String partId,
        String partName,
        String revision,
        String lifecycleStatus,
        String ownerTeam,
        List<String> changeHistory,
        List<String> relatedDocuments
) {
}
