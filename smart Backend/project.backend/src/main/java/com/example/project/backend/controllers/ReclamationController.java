package com.example.project.backend.controllers;

import com.example.project.backend.entity.Reclamation;
import com.example.project.backend.services.ReclamationService.IReclamationService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/reclamation")
@CrossOrigin(origins = "http://localhost:4200/")
public class ReclamationController {
    private IReclamationService reclamationService;

    @PostMapping("/add")
    public Reclamation addReclamation(@RequestBody Reclamation reclamation) {
        return reclamationService.addReclamation(reclamation);
    }

    @GetMapping("/retrieve-all")
    public List<Reclamation> retrieveAllReclamations() {
        return reclamationService.retrieveAllReclamations();
    }

    @GetMapping("/retrieve/{id}")
    public Reclamation retrieveReclamation(@PathVariable("id") Long reclamationId) {
        return reclamationService.retrieveReclamation(reclamationId);
    }

    @GetMapping("/status/{id}")
    public String getReclamationStatus(@PathVariable("id") Long reclamationId) {
        Reclamation reclamation = reclamationService.retrieveReclamation(reclamationId);
        if (reclamation == null) return "NOT_FOUND";
        return reclamation.getStatus() != null ? reclamation.getStatus().name() : "UNKNOWN";
    }

    @PutMapping("/modify")
    public Reclamation modifyReclamation(@RequestBody Reclamation reclamation) {
        return reclamationService.updateReclamation(reclamation);
    }

    @DeleteMapping("/remove/{id}")
    public void removeReclamation(@PathVariable("id") Long reclamationId) {
        reclamationService.deleteReclamation(reclamationId);
    }

}
