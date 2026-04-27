package com.example.project.backend.controllers;

import com.example.project.backend.entity.Adherent;
import com.example.project.backend.repositories.AdherentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/adherent")
public class AdherentController {

    @Autowired
    private AdherentRepository adherentRepository;

    @GetMapping("/{id}")
    public ResponseEntity<Adherent> getAdherent(@PathVariable Long id) {
        return adherentRepository.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
} 