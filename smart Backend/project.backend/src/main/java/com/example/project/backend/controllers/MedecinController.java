package com.example.project.backend.controllers;

import com.example.project.backend.entity.Medecin;
import com.example.project.backend.repositories.MedecinRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/medecin")
public class MedecinController {

    @Autowired
    private MedecinRepository medecinRepository;

    @GetMapping("/{id}")
    public ResponseEntity<Medecin> getMedecin(@PathVariable Long id) {
        return medecinRepository.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
} 