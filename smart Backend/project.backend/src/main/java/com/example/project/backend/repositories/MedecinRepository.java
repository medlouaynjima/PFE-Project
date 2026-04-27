package com.example.project.backend.repositories;

import com.example.project.backend.entity.Medecin;
import com.example.project.backend.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface MedecinRepository extends JpaRepository<Medecin,Long> {
    Optional<Medecin> findByUser(User user);
}
