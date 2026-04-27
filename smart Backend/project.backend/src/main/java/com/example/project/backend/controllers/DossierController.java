package com.example.project.backend.controllers;


import com.example.project.backend.entity.Dossier;
import com.example.project.backend.services.DossierService.IDossierService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/dossier")
@CrossOrigin(origins = "http://localhost:4200/")
public class DossierController {
    private IDossierService dossierService;

    @GetMapping("/retrieve-all")
    public List<Dossier> retrieveAllDossiers() {
        return dossierService.retrieveAllDossiers();
    }

    @GetMapping("/retrieve/{id}")
    public Dossier retrieveDossier(@PathVariable("id") Long dossierId) {
        return dossierService.retrieveDossier(dossierId);
    }

    @PostMapping("/add")
    public Dossier addDossier(@RequestBody Dossier dossier) {
        return dossierService.addDossier(dossier);
    }

    @DeleteMapping("/remove/{id}")
    public void removeDossier(@PathVariable("id") Long dossierId) {
        dossierService.deleteDossier(dossierId);
    }

    @PutMapping("/modify")
    public Dossier modifyDossier(@RequestBody Dossier dossier) {
        return dossierService.updateDossier(dossier);
    }



}