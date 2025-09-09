# brain_visualization.py
import matplotlib.pyplot as plt

from brain_dashboard.atlas_utils import AtlasUtils

plt.style.use('tableau-colorblind10')  # Clean, modern matplotlib style
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

pio.templates.default = 'plotly_white'  # Clean, modern plotly style
from nilearn import plotting, datasets, surface


class BrainVisualization:
    """Class for real brain visualization"""

    def __init__(self):
        # Load standard brain surfaces
        self.fsaverage = datasets.fetch_surf_fsaverage()

        # Load brain region atlas
        self.atlas = datasets.fetch_atlas_destrieux_2009()
        self.aparc = datasets.fetch_atlas_surf_destrieux()

    def create_3d_brain_plotly(self, region_values, colorscale='RdBu_r', title='Brain Regions'):
        """Create interactive 3D brain with Plotly"""

        # Load brain surfaces
        mesh_left = surface.load_surf_mesh(self.fsaverage['pial_left'])
        mesh_right = surface.load_surf_mesh(self.fsaverage['pial_right'])

        fig = go.Figure()

        # Add left hemisphere
        fig.add_trace(go.Mesh3d(
            x=mesh_left[0][:, 0],
            y=mesh_left[0][:, 1],
            z=mesh_left[0][:, 2],
            i=mesh_left[1][:, 0],
            j=mesh_left[1][:, 1],
            k=mesh_left[1][:, 2],
            intensity=self._map_values_to_vertices(region_values, 'left'),
            colorscale=colorscale,
            name='Left Hemisphere',
            showscale=True,
            colorbar=dict(
                title=title,
                x=1.02
            )
        ))

        # Add right hemisphere
        fig.add_trace(go.Mesh3d(
            x=mesh_right[0][:, 0] + 80,  # Shift to the side
            y=mesh_right[0][:, 1],
            z=mesh_right[0][:, 2],
            i=mesh_right[1][:, 0],
            j=mesh_right[1][:, 1],
            k=mesh_right[1][:, 2],
            intensity=self._map_values_to_vertices(region_values, 'right'),
            colorscale=colorscale,
            name='Right Hemisphere',
            showscale=False
        ))

        # Update display
        fig.update_layout(
            scene=dict(
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, visible=False),
                yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, visible=False),
                zaxis=dict(showticklabels=False, showgrid=False, zeroline=False, visible=False),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=0.5)
                ),
                bgcolor='white'
            ),
            title=title,
            width=800,
            height=600,
            paper_bgcolor='white'
        )

        return fig

    def create_surface_brain_nilearn(self, region_values, views=['lateral', 'medial', 'ventral', 'dorsal'],
                                     hemisphere='both', cmap='RdBu_r', title=''):
        """Create brain images with nilearn"""

        # Map region values to surface heatmap
        texture_left = self._map_values_to_vertices(region_values, 'left')
        texture_right = self._map_values_to_vertices(region_values, 'right')

        # Create Figure
        if hemisphere == 'both':
            fig, axes = plt.subplots(2, len(views), figsize=(5 * len(views), 10),
                                     subplot_kw={'projection': '3d'})
            axes = axes.flatten()
        else:
            fig, axes = plt.subplots(1, len(views), figsize=(5 * len(views), 5),
                                     subplot_kw={'projection': '3d'})
            if len(views) == 1:
                axes = [axes]

        ax_idx = 0

        # Draw left hemisphere
        if hemisphere in ['left', 'both']:
            for view in views:
                plotting.plot_surf_stat_map(
                    self.fsaverage['pial_left'],
                    texture_left,
                    hemi='left',
                    view=view,
                    cmap=cmap,
                    bg_map=self.fsaverage['sulc_left'],
                    axes=axes[ax_idx],
                    colorbar=True if ax_idx == len(views) - 1 else False,
                    title=f'Left {view}' if hemisphere == 'both' else view
                )
                ax_idx += 1

        # Draw right hemisphere
        if hemisphere in ['right', 'both']:
            for view in views:
                plotting.plot_surf_stat_map(
                    self.fsaverage['pial_right'],
                    texture_right,
                    hemi='right',
                    view=view,
                    cmap=cmap,
                    bg_map=self.fsaverage['sulc_right'],
                    axes=axes[ax_idx],
                    colorbar=False,
                    title=f'Right {view}' if hemisphere == 'both' else view
                )
                ax_idx += 1

        fig.suptitle(title, fontsize=16)
        # plt.tight_layout()

        return fig

    def create_2d_glass_brain(self, region_coordinates, region_values,
                              node_size=None, cmap='RdBu_r', title=''):
        """
        Create a Glass Brain plot with points for brain regions.

        A glass brain is a 2D projection of the brain where regions are
        represented by dots. This function uses nilearn's plot_connectome
        to achieve this effect without showing any connections.

        Args:
            region_coordinates (list or array): A list of 3D coordinates for each region.
            region_values (list or array): The scalar value to be plotted for each region.
            node_size (list or array, optional): The size of each region's dot. If None,
                                                 it is calculated based on region_values.
            cmap (str, optional): The colormap to use for the region values.
            title (str, optional): The title of the plot.

        Returns:
            matplotlib.figure.Figure: The matplotlib figure object.
        """
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib import cm
        from nilearn import plotting

        norm = plt.Normalize(vmin=np.min(region_values), vmax=np.max(region_values))
        # Compute node size by values if not provided
        if node_size is None:
            min_val, max_val = np.min(np.abs(region_values)), np.max(np.abs(region_values))
            if max_val - min_val > 0:
                node_size = 30 + 70 * norm(region_values)  # Scale node size from 30 to 100
            else:
                node_size = np.full_like(region_values, 50)

        colormap = cm.get_cmap(cmap)
        node_colors = colormap(norm(region_values))

        # Use gridspec to allocate space for colorbar
        fig = plt.figure(figsize=(15, 8))
        gs = fig.add_gridspec(1, 2, width_ratios=[20, 1], wspace=0.05)
        ax_main = fig.add_subplot(gs[0, 0])
        ax_cbar = fig.add_subplot(gs[0, 1])

        # Plot connectome on the main axes
        display = plotting.plot_connectome(
            adjacency_matrix=np.zeros((len(region_values), len(region_values))),
            node_coords=region_coordinates,
            node_color=node_colors,
            node_size=node_size,
            edge_threshold=1.0,
            title=title,
            figure=fig,
            axes=ax_main,
            display_mode="lyrz",  # multiple projections
            colorbar=False
        )

        # Add colorbar to the colorbar axes
        plt.colorbar(cm.ScalarMappable(norm=norm, cmap=colormap), cax=ax_cbar)
        ax_cbar.set_ylabel('Value', rotation=270, labelpad=15)

        return fig

    def create_glass_brain(self, region_coordinates, region_values,
                           node_size=None, cmap='RdBu_r', title='', region_names=None):
        """
        Create an interactive Glass Brain plot with Plotly.

        This function uses Plotly's Scatter3d trace to create a 3D scatter plot
        of brain regions, which is fully interactive (rotate, zoom, hover).

        Args:
            region_coordinates (list or array): A list of 3D coordinates for each region.
            region_values (list or array): The scalar value to be plotted for each region.
            node_size (list or array, optional): The size of each region's dot. If None,
                                                 it is calculated based on region_values.
            cmap (str, optional): The colormap to use for the region values.
            title (str, optional): The title of the plot.

        Returns:
            plotly.graph_objects.Figure: The Plotly figure object.
        """

        # Compute node size by values if not provided
        if node_size is None:
            # Normalize absolute values for node size
            norm = plt.Normalize(vmin=np.min(region_values), vmax=np.max(region_values))

            min_val, max_val = np.min(np.abs(region_values)), np.max(np.abs(region_values))
            if max_val - min_val > 0:
                node_size = 30 + 70 * norm(region_values)  # Scale node size from 30 to 100
            else:  # Handle case where all values are the same
                node_size = np.full_like(region_values, 50)

        # Ensure numpy arrays
        coords = np.asarray(region_coordinates, dtype=float)
        values = np.asarray(region_values, dtype=float)
        if region_names is None:
            region_names = [f'Region {i + 1}' for i in range(len(values))]

        # Load brain surfaces for context (no artificial shifts)
        mesh_left_vertices, mesh_left_faces = surface.load_surf_mesh(self.fsaverage['pial_left'])
        mesh_right_vertices, mesh_right_faces = surface.load_surf_mesh(self.fsaverage['pial_right'])

        # Compute combined brain mesh bounds
        all_mesh_vertices = np.vstack([mesh_left_vertices, mesh_right_vertices])
        mesh_min = all_mesh_vertices.min(axis=0)
        mesh_max = all_mesh_vertices.max(axis=0)
        mesh_center = (mesh_min + mesh_max) / 2.0
        mesh_range = np.maximum(mesh_max - mesh_min, 1e-6)

        # Compute coords bounds and transform to mesh space so points sit inside the brain
        coords_min = coords.min(axis=0)
        coords_max = coords.max(axis=0)
        coords_center = (coords_min + coords_max) / 2.0
        coords_range = np.maximum(coords_max - coords_min, 1e-6)

        # Uniform scale to preserve aspect; map the largest extent to fit inside mesh
        scale_per_axis = mesh_range / coords_range
        uniform_scale = float(np.min(scale_per_axis))
        coords_aligned = (coords - coords_center) * uniform_scale + mesh_center
        # coords_aligned = coords

        # Clamp to brain bounding sphere to avoid points outside mesh envelope
        center_shifted_vertices = all_mesh_vertices - mesh_center
        sphere_radius = float(np.linalg.norm(center_shifted_vertices, axis=1).max())
        vectors = coords_aligned - mesh_center
        norms = np.linalg.norm(vectors, axis=1)
        too_far = norms > (0.99 * sphere_radius)
        if np.any(too_far):
            scale_back = (0.97 * sphere_radius) / np.maximum(norms[too_far], 1e-9)
            vectors[too_far] = vectors[too_far] * scale_back[:, None]
            coords_aligned = mesh_center + vectors

        # Create a Plotly Figure
        fig = go.Figure()

        # Add translucent brain meshes as context (glass brain effect)
        fig.add_trace(go.Mesh3d(
            x=mesh_left_vertices[:, 0],
            y=mesh_left_vertices[:, 1],
            z=mesh_left_vertices[:, 2],
            i=mesh_left_faces[:, 0],
            j=mesh_left_faces[:, 1],
            k=mesh_left_faces[:, 2],
            color='lightgray',
            opacity=0.22,
            name='Brain (L)',
            hoverinfo='skip',
            showlegend=True,
            flatshading=True,
            lighting=dict(ambient=0.9, diffuse=0.35, specular=0.0, roughness=1.0, fresnel=0.0)
        ))
        fig.add_trace(go.Mesh3d(
            x=mesh_right_vertices[:, 0],
            y=mesh_right_vertices[:, 1],
            z=mesh_right_vertices[:, 2],
            i=mesh_right_faces[:, 0],
            j=mesh_right_faces[:, 1],
            k=mesh_right_faces[:, 2],
            color='lightgray',
            opacity=0.22,
            name='Brain (R)',
            hoverinfo='skip',
            showlegend=True,
            flatshading=True,
            lighting=dict(ambient=0.9, diffuse=0.35, specular=0.0, roughness=1.0, fresnel=0.0)
        ))

        # Add a 3D scatter trace for the brain regions (aligned to mesh bounds)
        # Prepare colorscale and reversal for Plotly
        reversescale = False
        plotly_colorscale = cmap
        if isinstance(cmap, str) and cmap.endswith('_r'):
            reversescale = True
            plotly_colorscale = cmap[:-2]

        fig.add_trace(go.Scatter3d(
            x=coords_aligned[:, 0],
            y=coords_aligned[:, 1],
            z=coords_aligned[:, 2],
            mode='markers+text',
            text=[f'{name}<br>Value: {val:.3f}' for name, val in zip(region_names, values)],
            textposition="top center",  # small label above each point
            hoverinfo='text',
            hovertemplate='%{text}<extra></extra>',
            marker=dict(
                size=(8 if node_size is None else (np.asarray(node_size, dtype=float) / 6.0)),
                color=values,
                colorscale=plotly_colorscale,
                colorbar=dict(title='Region Value'),
                line=dict(width=0.5, color='DarkSlateGrey'),
                opacity=0.95,
                reversescale=reversescale,
            ),
            # hoverinfo='text',
            # text=[f'{name}<br>Value: {val:.3f}' for name, val in zip(region_names, values)],
            # hovertemplate='%{text}<extra></extra>',
            name='Regions'
        ))

        # Update the layout for a cleaner look
        fig.update_layout(
            scene=dict(
                xaxis_title='',
                yaxis_title='',
                zaxis_title='',
                xaxis=dict(showbackground=False, showticklabels=False, zeroline=False, visible=False),
                yaxis=dict(showbackground=False, showticklabels=False, zeroline=False, visible=False),
                zaxis=dict(showbackground=False, showticklabels=False, zeroline=False, visible=False),
                bgcolor='white',
                aspectmode='data',
                camera=dict(eye=dict(x=1.6, y=1.6, z=0.8))
            ),
            title=title,
            width=800,
            height=600,
            paper_bgcolor='white',
            showlegend=True,
            legend=dict(itemsizing='constant'),
            dragmode='orbit',
            clickmode='event+select',
            uirevision='glass_brain',
            updatemenus=[dict(
                type='buttons',
                direction='left',
                buttons=[
                    dict(
                        label='Hide Brain',
                        method='update',
                        args=[
                            {'visible': [False, False, True]},
                            {'title': title}
                        ]
                    ),
                    dict(
                        label='Show Brain',
                        method='update',
                        args=[
                            {'visible': [True, True, True]},
                            {'title': title}
                        ]
                    )
                ],
                x=0.0, y=1.08, xanchor='left', yanchor='top',
                pad=dict(t=2, r=2)
            )]
        )

        return fig

    # Mapping from Desikan-Killiany (aparc) to Destrieux atlas indices
    def _map_values_to_vertices(self, region_values, hemisphere):
        """Create value texture for brain surface"""
        if hemisphere == 'left':
            labels = self.aparc['map_left']
        else:
            labels = self.aparc['map_right']

        texture = np.zeros(len(labels), dtype=float)

        for region_name, value in region_values.items():
            # Clean region name (remove '_area' suffix if present)
            clean_name = region_name.replace('_area', '')

            # Get the Destrieux index
            region_idx = AtlasUtils.get_aparc_to_destrieux_mapping(clean_name)
            # Apply value to all vertices with this label
            texture[labels == region_idx] = value

        return texture
