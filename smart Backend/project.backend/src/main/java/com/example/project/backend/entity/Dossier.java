package com.example.project.backend.entity;

import jakarta.persistence.*;

import java.io.Serializable;
import java.util.Objects;


@Entity
@Table(name = "DOSSIER")
public class Dossier implements Serializable {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "ID")
    private Long id;

    @Column(name = "TICKET_MOD")
    private Long ticketModerateur;

    @Column(name = "REST_A_PAYER")
    private Float resteAPayer;

    @Column(name = "PHARMACIE")
    private Boolean pharmacie;

    @Column(name = "RADIO")
    private Boolean radio;

    @Column(name = "ANALYSES")
    private Boolean analyses;

    @Column(name = "AUTRE")
    private Boolean autre;

    @ManyToOne
    @JoinColumn(name = "ID_MALADE")
    private MaladeEnCharge maladeEnCharge;

    @ManyToOne
    @JoinColumn(name = "ID_MEDECIN")
    private Medecin medecin;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getTicketModerateur() {
        return ticketModerateur;
    }

    public void setTicketModerateur(Long ticketModerateur) {
        this.ticketModerateur = ticketModerateur;
    }

    public Float getResteAPayer() {
        return resteAPayer;
    }

    public void setResteAPayer(Float resteAPayer) {
        this.resteAPayer = resteAPayer;
    }

    public Boolean getPharmacie() {
        return pharmacie;
    }

    public void setPharmacie(Boolean pharmacie) {
        this.pharmacie = pharmacie;
    }

    public Boolean getRadio() {
        return radio;
    }

    public void setRadio(Boolean radio) {
        this.radio = radio;
    }

    public Boolean getAnalyses() {
        return analyses;
    }

    public void setAnalyses(Boolean analyses) {
        this.analyses = analyses;
    }

    public Boolean getAutre() {
        return autre;
    }

    public void setAutre(Boolean autre) {
        this.autre = autre;
    }

    public MaladeEnCharge getMaladeEnCharge() {
        return maladeEnCharge;
    }

    public void setMaladeEnCharge(MaladeEnCharge maladeEnCharge) {
        this.maladeEnCharge = maladeEnCharge;
    }

    public Medecin getMedecin() {
        return medecin;
    }

    public void setMedecin(Medecin medecin) {
        this.medecin = medecin;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Dossier dossier = (Dossier) o;
        return Objects.equals(id, dossier.id) && Objects.equals(ticketModerateur, dossier.ticketModerateur) && Objects.equals(resteAPayer, dossier.resteAPayer) && Objects.equals(pharmacie, dossier.pharmacie) && Objects.equals(radio, dossier.radio) && Objects.equals(analyses, dossier.analyses) && Objects.equals(autre, dossier.autre) && Objects.equals(maladeEnCharge, dossier.maladeEnCharge) && Objects.equals(medecin, dossier.medecin);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, ticketModerateur, resteAPayer, pharmacie, radio, analyses, autre, maladeEnCharge, medecin);
    }

    @Override
    public String toString() {
        return "Dossier{" +
                "id=" + id +
                ", ticketModerateur=" + ticketModerateur +
                ", resteAPayer=" + resteAPayer +
                ", pharmacie=" + pharmacie +
                ", radio=" + radio +
                ", analyses=" + analyses +
                ", autre=" + autre +
                ", maladeEnCharge=" + maladeEnCharge +
                ", medecin=" + medecin +
                '}';
    }
}
