package com.example.project.backend.repositories;

import com.example.project.backend.entity.Remboursement;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RemboursementRepository extends JpaRepository<Remboursement, Long> {
}
