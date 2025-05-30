use pyo3::prelude::*;

use std:: {
    collections::HashMap, fs::File, io::{BufReader, SeekFrom}, path::Path,
    io::Read, io::Seek,
};

use numpy:: {
    PyArray, PyArray2
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
    ) -> PyResult<(Py<PyArray<f32, numpy::Ix2>>, Py<PyArray<u32, numpy::Ix2>>)> {

        let path = Path::new(filename);
        let mut file = BufReader::new(File::open(path)?);

        let mut header = vec![0; 80];

        file.read_exact(&mut header)?;

        let (vertices, faces) = 
            if header[..5].eq_ignore_ascii_case(b"solid") {
                file.seek(SeekFrom::Start(0))?;
                Self::read_ascii_stl(&mut file)?
            } else {
                Self::read_binary_stl(&mut file)?
            };

        let vertices_array = PyArray::from_vec(py, &vertices).to_owned();
        let faces_array = PyArray::from_vec(py, &faces).to_owned();

        let vertices_final = vertices_array?.downcast::<PyArray2<f32>>()?;
        let faces_final = vertices_array?.downcast::<PyArray2<u32>>()?;

        Ok((vertices_final, faces_final))

    }
}

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn pyo3_pyvista_example(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
