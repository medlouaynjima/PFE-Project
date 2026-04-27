package com.example.project.backend.entity;

import com.example.project.backend.enums.StatusReclamation;
import jakarta.persistence.*;


import java.io.Serializable;
import java.util.Objects;


@Entity

@Table(name = "RECLAMATION")
public class Reclamation implements Serializable {

    @Id
    @Column(name = "ID")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    private StatusReclamation status;

    @Column(name = "TEXT_RECLAMATION")
    private String textReclamation;


    @ManyToOne
    @JoinColumn(name = "num_dossier")
    private Dossier dossier;

    @ManyToOne
    @JoinColumn(name = "matricule_agent")
    private Agent agent;


    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public StatusReclamation getStatus() {
        return status;
    }

    public void setStatus(StatusReclamation status) {
        this.status = status;
    }

    public String getTextReclamation() {
        return textReclamation;
    }

    public void setTextReclamation(String textReclamation) {
        this.textReclamation = textReclamation;
    }

    public Dossier getDossier() {
        return dossier;
    }

    public void setDossier(Dossier dossier) {
        this.dossier = dossier;
    }

    public Agent getAgent() {
        return agent;
    }

    public void setAgent(Agent agent) {
        this.agent = agent;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Reclamation that = (Reclamation) o;
        return Objects.equals(id, that.id) && status == that.status && Objects.equals(textReclamation, that.textReclamation) && Objects.equals(dossier, that.dossier) && Objects.equals(agent, that.agent);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, status, textReclamation, dossier, agent);
    }

    @Override
    public String toString() {
        return "Reclamation{" +
                "id=" + id +
                ", status=" + status +
                ", textReclamation='" + textReclamation + '\'' +
                ", dossier=" + dossier +
                ", agent=" + agent +
                '}';
    }

}
