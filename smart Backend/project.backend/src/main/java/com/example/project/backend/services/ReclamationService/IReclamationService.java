package com.example.project.backend.services.ReclamationService;

import com.example.project.backend.entity.Reclamation;

import java.util.List;

public interface IReclamationService {

    List<Reclamation> retrieveAllReclamations();
    Reclamation addReclamation(Reclamation reclamation);
    void deleteReclamation(Long id);
    Reclamation updateReclamation(Reclamation reclamation);
    Reclamation retrieveReclamation(Long id);

}
