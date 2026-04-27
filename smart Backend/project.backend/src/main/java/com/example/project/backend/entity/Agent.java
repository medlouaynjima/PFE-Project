package com.example.project.backend.entity;

import jakarta.persistence.*;

import java.io.Serializable;
import java.util.Objects;


@Entity
@Table(name = "AGENT")
public class Agent implements Serializable {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "ID")
    private Long id;

    @Column(name = "MAT_AGENT")
    private Long matriculeAgent;

    @Column(name = "GSM")
    private String gsm;

    @Column(name = "NOM")
    private String nom;

    @Column(name = "PRENOM")
    private String prenom;

    @ManyToOne
    @JoinColumn(name = "ID_USER")
    private User user;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getMatriculeAgent() {
        return matriculeAgent;
    }

    public void setMatriculeAgent(Long matriculeAgent) {
        this.matriculeAgent = matriculeAgent;
    }

    public String getGsm() {
        return gsm;
    }

    public void setGsm(String gsm) {
        this.gsm = gsm;
    }

    public String getNom() {
        return nom;
    }

    public void setNom(String nom) {
        this.nom = nom;
    }

    public String getPrenom() {
        return prenom;
    }

    public void setPrenom(String prenom) {
        this.prenom = prenom;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Agent agent = (Agent) o;
        return Objects.equals(id, agent.id) && Objects.equals(matriculeAgent, agent.matriculeAgent) && Objects.equals(gsm, agent.gsm) && Objects.equals(nom, agent.nom) && Objects.equals(prenom, agent.prenom) && Objects.equals(user, agent.user);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, matriculeAgent, gsm, nom, prenom, user);
    }

    @Override
    public String toString() {
        return "Agent{" +
                "id=" + id +
                ", matriculeAgent=" + matriculeAgent +
                ", gsm='" + gsm + '\'' +
                ", nom='" + nom + '\'' +
                ", prenom='" + prenom + '\'' +
                ", user=" + user +
                '}';
    }
}
