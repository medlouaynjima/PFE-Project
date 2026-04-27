package com.example.project.backend.services.AgentService;

import com.example.project.backend.entity.Agent;
import com.example.project.backend.repositories.AgentRepository;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
@Service
@AllArgsConstructor
public class AgentService implements IAgentService {

    AgentRepository agentRepository;


    @Override
    public List<Agent> retrieveAllAgents() {
        return agentRepository.findAll();
    }

    @Override
    public Agent addAgent(Agent agent) {
        agentRepository.save(agent);
        return agent;
    }

    @Override
    public void deleteAgent(Long id) {
        agentRepository.deleteById(id);
    }

    @Override
    public Agent updateAgent(Agent agent) {
        agentRepository.save(agent);
        return agent;
    }

    @Override
    public Agent retrieveAgent(Long id) {
        return agentRepository.findById(id).orElse(null);
    }
}
