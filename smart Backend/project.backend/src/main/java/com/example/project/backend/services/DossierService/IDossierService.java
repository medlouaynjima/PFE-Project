package com.example.project.backend.services.DossierService;

import com.example.project.backend.entity.Dossier;

import java.util.List;

public interface IDossierService {

    List<Dossier> retrieveAllDossiers();
    Dossier addDossier(Dossier dossier);
    void deleteDossier(Long id);
    Dossier updateDossier(Dossier dossier);
    Dossier retrieveDossier(Long id);

}
