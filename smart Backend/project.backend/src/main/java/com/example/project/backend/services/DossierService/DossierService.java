package com.example.project.backend.services.DossierService;


import com.example.project.backend.entity.Dossier;
import com.example.project.backend.repositories.DossierRepository;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@AllArgsConstructor
public class DossierService implements IDossierService {
    DossierRepository dossierRepository;

    @Override
    public List<Dossier> retrieveAllDossiers() {
        return dossierRepository.findAll();
    }

    @Override
    public Dossier addDossier(Dossier dossier) {
        dossierRepository.save(dossier);
        return dossier;
    }

    @Override
    public void deleteDossier(Long id) {
        dossierRepository.deleteById(id);
    }

    @Override
    public Dossier updateDossier(Dossier dossier) {
        dossierRepository.save(dossier);
        return dossier;
    }

    @Override
    public Dossier retrieveDossier(Long id) {
        return dossierRepository.findById(id).orElse(null);
    }
}
