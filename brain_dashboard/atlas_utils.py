# atlas_utils.py


class AtlasUtils:
    @staticmethod
    def get_aparc_to_destrieux_mapping(aparc_label):
        if aparc_label in ['BrainSegVol', 'BrainSegVolNotVent', 'eTIV',
                           'lhCortexVol', 'rhCortexVol', 'CortexVol',
                           'lhCerebralWhiteMatterVol', 'rhCerebralWhiteMatterVol',
                           'CerebralWhiteMatterVol', 'SubCortGrayVol', 'TotalGrayVol',
                           'SupraTentorialVol', 'SupraTentorialVolNotVent', 'MaskVol',
                           'BrainSegVol-to-eTIV', 'MaskVol-to-eTIV', 'lhSurfaceHoles',
                           'rhSurfaceHoles', 'SurfaceHoles', 'EstimatedTotalIntraCranialVol']:
            return 0  # No mapping for these summary measures

        # Comprehensive mapping from FreeSurfer aparc to Destrieux indices
        # Destrieux has 74 regions per hemisphere (indices 0-73 for left, 74-147 for right)
        # Index 0 is typically "unknown" or medial wall

        aparc_to_destrieux = {
            # LEFT HEMISPHERE (indices 1-73)
            # Frontal Lobe
            'lh_superiorfrontal': 28,  # G_front_sup
            'lh_rostralmiddlefrontal': 27,  # G_front_middle (rostral part)
            'lh_caudalmiddlefrontal': 27,  # G_front_middle (caudal part)
            'lh_parsopercularis': 24,  # G_front_inf-Opercular
            'lh_parstriangularis': 26,  # G_front_inf-Triangul
            'lh_parsorbitalis': 25,  # G_front_inf-Orbital
            'lh_lateralorbitofrontal': 36,  # G_orbital
            'lh_medialorbitofrontal': 43,  # G_rectus + G_subcallosal
            'lh_precentral': 41,  # G_precentral
            'lh_paracentral': 17,  # G_and_S_paracentral
            'lh_frontalpole': 19,  # G_and_S_transv_frontopol

            # Parietal Lobe
            'lh_superiorparietal': 39,  # G_parietal_sup
            'lh_inferiorparietal': 37,  # G_pariet_inf-Angular
            'lh_supramarginal': 38,  # G_pariet_inf-Supramar
            'lh_postcentral': 40,  # G_postcentral
            'lh_precuneus': 42,  # G_precuneus

            # Temporal Lobe
            'lh_superiortemporal': 46,  # G_temp_sup-Lateral
            'lh_middletemporal': 50,  # G_temporal_middle
            'lh_inferiortemporal': 49,  # G_temporal_inf
            'lh_bankssts': 45,  # G_temp_sup-G_T_transv (banks of STS)
            'lh_fusiform': 33,  # G_oc-temp_lat-fusifor
            'lh_transversetemporal': 45,  # G_temp_sup-G_T_transv
            'lh_entorhinal': 21,  # S_collat_transv_post (approximate)
            'lh_temporalpole': 47,  # G_temp_sup-Plan_polar
            'lh_parahippocampal': 35,  # G_oc-temp_med-Parahip

            # Occipital Lobe
            'lh_lateraloccipital': 31,  # G_occipital_middle
            'lh_lingual': 34,  # G_oc-temp_med-Lingual
            'lh_cuneus': 23,  # G_cuneus
            'lh_pericalcarine': 32,  # G_occipital_sup + S_calcarine

            # Cingulate
            'lh_rostralanteriorcingulate': 20,  # G_and_S_cingul-Ant
            'lh_caudalanteriorcingulate': 20,  # G_and_S_cingul-Ant
            'lh_posteriorcingulate': 22,  # G_and_S_cingul-Mid-Post
            'lh_isthmuscingulate': 22,  # G_and_S_cingul-Mid-Post

            # Insula
            'lh_insula': 29,  # G_Ins_lg_and_S_cent_ins + G_insular_short
        }

        # Add right hemisphere by adding 74 to left indices
        for key, value in list(aparc_to_destrieux.items()):
            if key.startswith('lh_'):
                rh_key = key.replace('lh_', 'rh_')
                aparc_to_destrieux[rh_key] = value + 74

        return aparc_to_destrieux[aparc_label] if aparc_label in aparc_to_destrieux else 0

    @staticmethod
    def get_coordinates_for_region(region):
        region_coordinates = {
            # Subcortical structures (bilateral shown as left/right)
            'Left-Hippocampus': [-28, -18, -16],
            'Right-Hippocampus': [28, -18, -16],
            'Left-Amygdala': [-24, -6, -18],
            'Right-Amygdala': [24, -6, -18],
            'Left-Thalamus': [-11, -18, 8],
            'Right-Thalamus': [11, -18, 8],
            'Left-Caudate': [-13, 12, 9],
            'Right-Caudate': [13, 12, 9],
            'Left-Putamen': [-25, 0, 0],
            'Right-Putamen': [25, 0, 0],
            'Left-Pallidum': [-18, -4, -2],
            'Right-Pallidum': [18, -4, -2],
            'Left-Accumbens-area': [-9, 9, -8],
            'Right-Accumbens-area': [9, 9, -8],

            # Cerebellum
            'Left-Cerebellum-Cortex': [-20, -60, -40],
            'Right-Cerebellum-Cortex': [20, -60, -40],

            # Brain stem
            'Brain-Stem': [0, -24, -30],

            # Major cortical regions (approximate centers)
            'Frontal': [0, 30, 40],
            'Left-Frontal': [-30, 30, 40],
            'Right-Frontal': [30, 30, 40],
            'Temporal': [50, -20, -10],
            'Left-Temporal': [-50, -20, -10],
            'Right-Temporal': [50, -20, -10],
            'Parietal': [30, -50, 50],
            'Left-Parietal': [-30, -50, 50],
            'Right-Parietal': [30, -50, 50],
            'Occipital': [15, -85, 15],
            'Left-Occipital': [-15, -85, 15],
            'Right-Occipital': [15, -85, 15],

            # Specific cortical areas from aparc
            'lh_superiorfrontal': [-15, 35, 40],
            'rh_superiorfrontal': [15, 35, 40],
            'lh_precentral': [-40, -6, 50],
            'rh_precentral': [40, -6, 50],
            'lh_postcentral': [-40, -25, 50],
            'rh_postcentral': [40, -25, 50],
            'lh_superiortemporal': [-55, -20, 5],
            'rh_superiortemporal': [55, -20, 5],
            'lh_inferiorparietal': [-45, -55, 45],
            'rh_inferiorparietal': [45, -55, 45],
            'lh_precuneus': [-10, -65, 40],
            'rh_precuneus': [10, -65, 40],
        }
        return region_coordinates[region] if region in region_coordinates else None
