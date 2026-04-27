package com.example.project.backend.services.RemboursementService;


import com.example.project.backend.entity.Remboursement;
import com.example.project.backend.repositories.RemboursementRepository;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@AllArgsConstructor
public class RemboursementService implements IRemboursementService {

    RemboursementRepository remboursementRepository;

    @Override
    public List<Remboursement> retrieveAllRemboursements() {
        return remboursementRepository.findAll();
    }

    @Override
    public Remboursement addRemboursement(Remboursement remboursement) {
        remboursementRepository.save(remboursement);
        return remboursement;
    }

    @Override
    public void deleteRemboursement(Long id) {
        remboursementRepository.deleteById(id);
    }

    @Override
    public Remboursement updateRemboursement(Remboursement remboursement) {
        remboursementRepository.save(remboursement);
        return remboursement;
    }

    @Override
    public Remboursement retrieveRemboursement(Long id) {
        return remboursementRepository.findById(id).orElse(null);
    }

}
