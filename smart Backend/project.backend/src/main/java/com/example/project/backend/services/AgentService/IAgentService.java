package com.example.project.backend.services.AgentService;

import com.example.project.backend.entity.Agent;

import java.util.List;

public interface IAgentService {

    List<Agent> retrieveAllAgents();
    Agent addAgent(Agent agent);
    void deleteAgent(Long id);
    Agent updateAgent(Agent agent);
    Agent retrieveAgent(Long id);

}
