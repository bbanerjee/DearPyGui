use byteorder::LittleEndian;
use byteorder::ReadBytesExt;
use pyo3::prelude::*;

use std:: {
    collections::HashMap, fs::File, io::{BufReader, SeekFrom}, path::Path,
    io::Read, io::Seek,
    io::Result,
    io::Error, io::ErrorKind,
};

use numpy:: {
    PyArray
};

#[pyclass]
pub struct StlReader;

#[pymethods]
impl StlReader {

    #[new]
    fn new() -> Self {
        StlReader
    }

    pub fn read_stl<'py>(
        &self,
        py: Python<'py>,
        filename: &str,
    ) -> PyResult<(Py<PyArray<f32, numpy::Ix1>>, Py<PyArray<u32, numpy::Ix1>>)> {

        let path = Path::new(filename);
        let mut file = BufReader::new(File::open(path)?);

        let mut header = vec![0; 80];

        file.read_exact(&mut header)?;

        let (vertices, faces) = 
            if header[..5].eq_ignore_ascii_case(b"solid") {
                file.seek(SeekFrom::Start(0))?;
                Self::read_ascii_stl(&mut file)?
            } else {
                println!("Reading binary stl");
                Self::read_binary_stl(&mut file)?
            };

        let flat_vert: Vec<f32> = vertices.into_iter().flatten().collect();
        let flat_face: Vec<u32> = faces.into_iter().flatten().collect();
        let vertices_array = PyArray::from_vec(py, flat_vert);
        let faces_array = PyArray::from_vec(py, flat_face);

        /*
        let num_vert = vertices.len();
        let num_face = faces.len();
        let vertices_final = 
            PyArray2::from_vec2(py, &vec![flat_vert])
                .unwrap()
                .reshape((num_vert, 3))
                .unwrap()
                .to_owned();
        let faces_final = 
            PyArray2::from_vec2(py, &vec![flat_face])
                .unwrap()
                .reshape((num_face, 3))
                .unwrap()
                .to_owned();

        Ok((vertices_final.into(), faces_final.into()))
        */

        Ok((vertices_array.into(), faces_array.into()))

    }
}

impl StlReader {

    fn quantize_coord(val: f32, precision: f32) -> i64 {
        (val / precision).round() as i64
    }

    fn quantize_vert(vert: [f32; 3], precision: f32) -> [i64; 3] {
        [
            Self::quantize_coord(vert[0], precision),
            Self::quantize_coord(vert[1], precision),
            Self::quantize_coord(vert[2], precision),
        ]
    }

    fn read_binary_stl<R: Read + Seek>(
        f: &mut R,
    ) -> Result<(Vec<[f32; 3]>, Vec<[u32; 3]>)> {

        f.seek(SeekFrom::Start(80))?;

        let num_tri = f.read_u32::<LittleEndian>()?;
        println!("num_tri {}", num_tri);

        let mut verts: Vec<[f32; 3]> = Vec::new();
        let mut faces: Vec<[u32; 3]> = Vec::new();

        let mut vert_map: HashMap<[i64; 3], u32> = HashMap::new();
        let precision = 1.0e-6;

        for _ in 0..num_tri {
            f.seek(SeekFrom::Current(12))?;

            let mut tri_verts: Vec<u32> = Vec::with_capacity(3);
            for _ in 0..3 {
                let x = f.read_f32::<LittleEndian>()?;
                let y = f.read_f32::<LittleEndian>()?;
                let z = f.read_f32::<LittleEndian>()?;

                let vert = [x, y, z];
                println!("vert = {}{}{} ", x, y, z);

                let i64_vert = Self::quantize_vert(vert, precision);

                let vert_idx = if let Some(&existing_idx) = vert_map.get(&i64_vert) {
                    existing_idx
                } else {
                    let new_idx = verts.len() as u32;
                    verts.push(vert);
                    vert_map.insert(i64_vert, new_idx);
                    new_idx
                };

                tri_verts.push(vert_idx);
            }

            let _ = f.seek(SeekFrom::Current(2));

            if tri_verts.len() == 3 {
                faces.push([
                    tri_verts[0],
                    tri_verts[1],
                    tri_verts[2],
                ]);
            }
        }

        Ok((verts, faces))

    }

    fn read_ascii_stl<R: Read>(
        f: &mut R,
    ) -> Result<(Vec<[f32; 3]>, Vec<[u32; 3]>)> {

        let mut verts: Vec<[f32; 3]> = Vec::new();
        let mut faces: Vec<[u32; 3]> = Vec::new();

        let mut vert_map: HashMap<[i64; 3], u32> = HashMap::new();
        let precision = 1.0e-6;

        let mut data = String::new();

        f.read_to_string(&mut data)?;

        let lines: Vec<&str> = data.lines().collect();

        let mut i = 0;

        while i < lines.len() {

            let line = lines[i].trim().to_lowercase();
            if line.starts_with("facet normal") {
                i += 2;

                let mut tri_verts: Vec<u32> = Vec::with_capacity(3);
                for _ in 0..3 {

                    if i < lines.len() {
                        let vert_line = lines[i].trim();
                        if vert_line.starts_with("vertex") {

                            let coords_str: Vec<&str> = 
                                vert_line.split_whitespace().skip(1).take(3).collect();
                            if coords_str.len() == 3 {
                                let x = coords_str[0].parse::<f32>().map_err(
                                    |e| {
                                        Error::new(ErrorKind::InvalidData, e.to_string())
                                    })?;
                                let y = coords_str[1].parse::<f32>().map_err(
                                    |e| {
                                        Error::new(ErrorKind::InvalidData, e.to_string())
                                    })?;
                                let z = coords_str[2].parse::<f32>().map_err(
                                    |e| {
                                        Error::new(ErrorKind::InvalidData, e.to_string())
                                    })?;

                                let vert = [x, y, z];

                                let i64_vert = Self::quantize_vert(vert, precision);

                                let vert_idx = if let Some(&existing_idx) = vert_map.get(&i64_vert) {
                                    existing_idx
                                } else {
                                    let new_idx = verts.len() as u32;
                                    verts.push(vert);
                                    vert_map.insert(i64_vert, new_idx);
                                    new_idx
                                };

                                tri_verts.push(vert_idx);
                            }
                        }
                    }
                    i += 1;
                }

                if tri_verts.len() == 3 {
                    faces.push([
                        tri_verts[0],
                        tri_verts[1],
                        tri_verts[2],
                    ]);
                }
            } else {
                i += 1;
            }
        }

        Ok((verts, faces))

    }

}

/// A Python module implemented in Rust.
#[pymodule]
fn pyo3_pyvista_example(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<StlReader>()?;
    Ok(())
}
