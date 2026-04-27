package com.example.project.backend.repositories;

import com.example.project.backend.entity.Adherent;
import com.example.project.backend.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface AdherentRepository extends JpaRepository<Adherent, Long> {
    Optional<Adherent> findByUser(User user);
} 