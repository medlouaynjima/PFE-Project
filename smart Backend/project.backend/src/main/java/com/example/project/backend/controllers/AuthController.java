package com.example.project.backend.controllers;

import com.example.project.backend.dto.AuthRequest;
import com.example.project.backend.services.JwtService;
import com.example.project.backend.entity.User;
import com.example.project.backend.entity.Adherent;
import com.example.project.backend.entity.Medecin;
import com.example.project.backend.repositories.UserRepository;
import com.example.project.backend.repositories.AdherentRepository;
import com.example.project.backend.repositories.MedecinRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/auth")
public class AuthController {

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private AdherentRepository adherentRepository;
    @Autowired
    private MedecinRepository medecinRepository;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody AuthRequest authRequest) {
        try {
            String login = authRequest.getEmail() != null && !authRequest.getEmail().isEmpty()
                    ? authRequest.getEmail()
                    : authRequest.getUsername();

            if (login == null || login.isEmpty()) {
                throw new RuntimeException("Email or username must be provided");
            }

            String userType = authRequest.getUserType(); // "adherent", "medecin", "admin"

            Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(login, authRequest.getPassword())
            );

            User user = userRepository.findByUsername(login)
                    .orElseGet(() -> userRepository.findByEmail(login).orElse(null));
            if (user == null) {
                return ResponseEntity.status(401).body("User not found");
            }

            String role = user.getRole().name(); // "ADHERENT", "MEDECIN", "ADMIN"

            // Vérification de cohérence
            if ((userType.equals("adherent") && !role.equals("ADHERENT")) ||
                (userType.equals("medecin") && !role.equals("MEDECIN")) ||
                (userType.equals("admin") && !role.equals("ADMIN"))) {
                return ResponseEntity.status(403).body("Ce compte n'existe pas pour ce type d'utilisateur.");
            }

            Long adherentId = null;
            Long medecinId = null;

            Map<String, Object> response = new HashMap<>();

            if (role.equals("ADHERENT")) {
                Adherent adherent = adherentRepository.findByUser(user).orElse(null);
                if (adherent != null) {
                    adherentId = adherent.getId();
                    response.put("nom", adherent.getNom());
                    response.put("prenom", adherent.getPrenom());
                }
            } else if (role.equals("MEDECIN")) {
                Medecin medecin = medecinRepository.findByUser(user).orElse(null);
                if (medecin != null) {
                    medecinId = medecin.getId();
                    response.put("nom", medecin.getNom());
                    response.put("prenom", medecin.getPrenom());
                }
            } else if (role.equals("ADMIN")) {
                response.put("username", user.getUsername());
            }

            String jwt = jwtService.generateToken(login);

            response.put("token", jwt);
            response.put("user_id", user.getId());
            response.put("role", role);
            response.put("adherent_id", adherentId);
            response.put("medecin_id", medecinId);

            return ResponseEntity.ok(response);

        } catch (AuthenticationException e) {
            return ResponseEntity.status(401).body("Invalid credentials");
        }
    }
} 