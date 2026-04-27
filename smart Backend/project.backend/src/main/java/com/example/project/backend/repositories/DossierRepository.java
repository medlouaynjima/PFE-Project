package com.example.project.backend.repositories;

import com.example.project.backend.entity.Dossier;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DossierRepository extends JpaRepository<Dossier,Long> {
}
