package com.example.legacymock.service;

public class LegacyResourceNotFoundException extends RuntimeException {
    public LegacyResourceNotFoundException(String message) {
        super(message);
    }
}
