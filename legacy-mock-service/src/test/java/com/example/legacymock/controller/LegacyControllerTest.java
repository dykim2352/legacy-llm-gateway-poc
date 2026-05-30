package com.example.legacymock.controller;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class LegacyControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    void erpOrderReturnsMockData() throws Exception {
        mockMvc.perform(get("/api/v1/legacy/erp/orders/ORD-1001"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.orderId").value("ORD-1001"))
                .andExpect(jsonPath("$.itemName").value("Tactical Network Module"));
    }

    @Test
    void pdmPartReturnsMockData() throws Exception {
        mockMvc.perform(get("/api/v1/legacy/pdm/parts/PART-2001"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.partId").value("PART-2001"))
                .andExpect(jsonPath("$.revision").value("R3"));
    }

    @Test
    void groupwareUserReturnsMockData() throws Exception {
        mockMvc.perform(get("/api/v1/legacy/groupware/users/USER-3001"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value("USER-3001"))
                .andExpect(jsonPath("$.roles[1]").value("APPROVER"));
    }

    @Test
    void missingLegacyResourceReturnsNotFound() throws Exception {
        mockMvc.perform(get("/api/v1/legacy/erp/orders/ORD-9999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.message", containsString("ORD-9999")));
    }

    @Test
    void actuatorHealthReturnsUp() throws Exception {
        mockMvc.perform(get("/actuator/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }
}
