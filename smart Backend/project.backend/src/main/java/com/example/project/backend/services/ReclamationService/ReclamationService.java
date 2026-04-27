package com.example.project.backend.services.ReclamationService;


import com.example.project.backend.entity.Reclamation;
import com.example.project.backend.repositories.ReclamationRepository;
import com.example.project.backend.services.NotificationService;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@AllArgsConstructor
public class ReclamationService implements IReclamationService {

    ReclamationRepository reclamationRepository;
    private final NotificationService notificationService;

    @Override
    public List<Reclamation> retrieveAllReclamations() {
        return reclamationRepository.findAll();
    }

    @Override
    public Reclamation addReclamation(Reclamation reclamation) {
        reclamationRepository.save(reclamation);
        return reclamation;
    }

    @Override
    public void deleteReclamation(Long id) {
        reclamationRepository.deleteById(id);
    }

    @Override
    public Reclamation updateReclamation(Reclamation reclamation) {
        reclamationRepository.save(reclamation);
        // Get the user's email (adherent or medecin)
        String email = null;
        if (reclamation.getDossier() != null) {
            if (reclamation.getDossier().getMaladeEnCharge() != null &&
                reclamation.getDossier().getMaladeEnCharge().getAdherent() != null &&
                reclamation.getDossier().getMaladeEnCharge().getAdherent().getUser() != null) {
                email = reclamation.getDossier().getMaladeEnCharge().getAdherent().getUser().getEmail();
            } else if (reclamation.getDossier().getMedecin() != null &&
                       reclamation.getDossier().getMedecin().getUser() != null) {
                email = reclamation.getDossier().getMedecin().getUser().getEmail();
            }
        }
        // Send notification if email found
        if (email != null) {
            String subject = "Mise à jour de votre réclamation";
            String text = "Votre réclamation #" + reclamation.getId() +
                          " a changé de statut : " + reclamation.getStatus();
            notificationService.sendStatusUpdateEmail(email, subject, text);
        }
        return reclamation;
    }

    @Override
    public Reclamation retrieveReclamation(Long id) {
        return reclamationRepository.findById(id).orElse(null);
    }

}
