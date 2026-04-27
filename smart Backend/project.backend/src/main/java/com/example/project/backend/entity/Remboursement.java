package com.example.project.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Objects;


@Entity

@Table(name = "REMBOURSEMENT")
public class Remboursement implements Serializable {

    @Id
    @Column(name = "ID")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long idRemboursement;

    @Column(name = "TOTALE_REMBOURSE")
    private Float totalRembourse;

    @Column(name = "EST_REMBOURSE")
    private Boolean estrembourse;

    @Column(name = "DATE_DECISION")
    private String dataDecision;

    @Column(name = "TOTAL_ORDONNANCE")
    private Float totalOrdonnance;

    @ManyToOne
    @JoinColumn(name = "ID_DOSSIER")
    private Dossier dossier;


    public Long getIdRemboursement() {
        return idRemboursement;
    }

    public void setIdRemboursement(Long idRemboursement) {
        this.idRemboursement = idRemboursement;
    }

    public Float getTotalRembourse() {
        return totalRembourse;
    }

    public void setTotalRembourse(Float totalRembourse) {
        this.totalRembourse = totalRembourse;
    }

    public Boolean getEstrembourse() {
        return estrembourse;
    }

    public void setEstrembourse(Boolean estrembourse) {
        this.estrembourse = estrembourse;
    }

    public String getDataDecision() {
        return dataDecision;
    }

    public void setDataDecision(String dataDecision) {
        this.dataDecision = dataDecision;
    }

    public Float getTotalOrdonnance() {
        return totalOrdonnance;
    }

    public void setTotalOrdonnance(Float totalOrdonnance) {
        this.totalOrdonnance = totalOrdonnance;
    }

    public Dossier getDossier() {
        return dossier;
    }

    public void setDossier(Dossier dossier) {
        this.dossier = dossier;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Remboursement that = (Remboursement) o;
        return Objects.equals(idRemboursement, that.idRemboursement) && Objects.equals(totalRembourse, that.totalRembourse) && Objects.equals(estrembourse, that.estrembourse) && Objects.equals(dataDecision, that.dataDecision) && Objects.equals(totalOrdonnance, that.totalOrdonnance) && Objects.equals(dossier, that.dossier);
    }

    @Override
    public int hashCode() {
        return Objects.hash(idRemboursement, totalRembourse, estrembourse, dataDecision, totalOrdonnance, dossier);
    }

    @Override
    public String toString() {
        return "Remboursement{" +
                "idRemboursement=" + idRemboursement +
                ", totalRembourse=" + totalRembourse +
                ", estrembourse=" + estrembourse +
                ", dataDecision='" + dataDecision + '\'' +
                ", totalOrdonnance=" + totalOrdonnance +
                ", dossier=" + dossier +
                '}';
    }
}
