package com.example.project.backend.controllers;

import com.example.project.backend.entity.Remboursement;
import com.example.project.backend.services.DossierService.IDossierService;
import com.example.project.backend.services.RemboursementService.IRemboursementService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/remboursement")
@CrossOrigin(origins = "http://localhost:4200/")
public class RemboursementController {
    private IRemboursementService remboursementService;

    @GetMapping("/retrieve-all")
    public List<Remboursement> retrieveAllRemboursements() {
        return remboursementService.retrieveAllRemboursements();
    }

    @GetMapping("/retrieve/{id}")
    public Remboursement retrieveRemboursement(@PathVariable("id") Long remboursementId) {
        return remboursementService.retrieveRemboursement(remboursementId);
    }

    @PostMapping("/add")
    public Remboursement addRemboursement(@RequestBody Remboursement remboursement) {
        return remboursementService.addRemboursement(remboursement);
    }

    @DeleteMapping("/remove/{id}")
    public void removeRemboursement(@PathVariable("id") Long remboursementId) {
        remboursementService.deleteRemboursement(remboursementId);
    }

    @PutMapping("/modify")
    public Remboursement modifyRemboursement(@RequestBody Remboursement remboursement) {
        return remboursementService.updateRemboursement(remboursement);
    }

}
