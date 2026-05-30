package com.example.legacymock.connector;

import java.util.Optional;

public interface LegacyConnector<ID, R> {
    Optional<R> findById(ID id);
}
