package com.example.project.backend.services.RemboursementService;

import com.example.project.backend.entity.Remboursement;

import java.util.List;

public interface IRemboursementService {

    List<Remboursement> retrieveAllRemboursements();
    Remboursement addRemboursement(Remboursement remboursement);
    void deleteRemboursement(Long id);
    Remboursement updateRemboursement(Remboursement remboursement);
    Remboursement retrieveRemboursement(Long id);

}
