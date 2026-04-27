package com.example.project.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Date;
import java.util.Objects;

@Entity
@Table(name = "RECLAMATIONRESOLU")
public class ReclamationResolu implements Serializable {
    

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "ID")
    private Long id;

    @Column(name = "DATE_RESOLUTION")
    @Temporal(TemporalType.TIMESTAMP)
    private Date dateResolution;

    @Column(name = "COMMENTAIRE_RESOLUTION")
    private String commentaireResolution;

    @OneToOne
    @JoinColumn(name = "ID_RECLAMATION")
    private Reclamation reclamation;

    @ManyToOne
    @JoinColumn(name = "ID_AGENT")
    private Agent agent;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Date getDateResolution() {
        return dateResolution;
    }

    public void setDateResolution(Date dateResolution) {
        this.dateResolution = dateResolution;
    }

    public String getCommentaireResolution() {
        return commentaireResolution;
    }

    public void setCommentaireResolution(String commentaireResolution) {
        this.commentaireResolution = commentaireResolution;
    }

    public Reclamation getReclamation() {
        return reclamation;
    }

    public void setReclamation(Reclamation reclamation) {
        this.reclamation = reclamation;
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
        ReclamationResolu that = (ReclamationResolu) o;
        return Objects.equals(id, that.id) && Objects.equals(dateResolution, that.dateResolution) && Objects.equals(commentaireResolution, that.commentaireResolution) && Objects.equals(reclamation, that.reclamation) && Objects.equals(agent, that.agent);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, dateResolution, commentaireResolution, reclamation, agent);
    }

    @Override
    public String toString() {
        return "ReclamationResolu{" +
                "id=" + id +
                ", dateResolution=" + dateResolution +
                ", commentaireResolution='" + commentaireResolution + '\'' +
                ", reclamation=" + reclamation +
                ", agent=" + agent +
                '}';
    }
}