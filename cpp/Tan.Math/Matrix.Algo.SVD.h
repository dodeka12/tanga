//////////////////////////////////////////////////////////////////////////////////
// <<licence: start>>
//
// This file is part of the TANGA library, 
// a template library that implements geometric algebra.
//
// Copyright 2022 Christian Perwass
//
//    Licensed under the Apache License, Version 2.0 (the "License");
//    you may not use this file except in compliance with the License.
//    You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS,
//    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//    See the License for the specific language governing permissions and
//    limitations under the License.
//
// <<licence: end>>
//////////////////////////////////////////////////////////////////////////////////

#pragma once

#define _USE_MATH_DEFINES
#include <math.h>
#include <iostream>
#include <string>

#include "Matrix.h"
#include "Matrix.Operators.h"

#define _MAXSVDITS_ 50

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// namespace: Tan
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
namespace Tan
{

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	/// <summary>
	/// 	A matrix mathematics.
	/// </summary>
	///
	/// <typeparam name="T"> Generic type parameter. </typeparam>
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	template<typename T>
	class CMatrixAlgoSVD
	{
	public:

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Calculate Singular Value Decomposition.
		/// </summary>
		///
		/// <param name="matU"> [in,out] The matrix u. </param>
		/// <param name="matD"> [in,out] The matrix d. </param>
		/// <param name="matV"> [in,out] The matrix v. </param>
		/// <param name="matA"> The matrix a. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		static void SVD(CMatrix<T>& matU, CMatrix<T>& matD, CMatrix<T>& matV, const CMatrix<T>& matA)
		{
			try
			{
				matU = matA;

				// Ensure that a possible transposition of matA is represented in memory,
				// since we are not working with iterators here.
				matU.ApplyToMemory();

				int iURP, iURPi, iURPj;
				int iVRP;
				int l, k, j, jj, iItCnt, i, rcmin, hi, hj;
				int iCols, iRows;
				int iCR;
				T tX, tY, tZ, tScale, tS, tH, tG, tF, tC, tAnorm;

				std::vector<T> vecRV1;

				iRows = int(matU.GetRowCount());
				iCols = int(matU.GetColCount());

				if (!iCols || !iRows)
				{
					TAN_THROW_RT("Invalid matrix");
				}

				vecRV1.resize(iCols);

				matV.SetSize(iCols, iCols);
				matD.SetSize(1, iCols);

				T* pUData = matU.GetDataPtr();
				T* pVData = matV.GetDataPtr();
				T* pWData = matD.GetDataPtr();

				/* Use the following for debugging array overshoots
				Mem<T> &udata = *mU.mat;
				Mem<T> &vdata = *mV.mat;
				Mem<T> &wdata = *mW.mat;
				*/

				tG     = T(0);
				tScale = T(0);
				tAnorm = T(0);

				// Householder reduction to bidiagonal form
				for (i = 0, l = 1; i < iCols; i++, l++)
				{
					iURPi = i * iCols;

					vecRV1[i] = tScale * tG;
					tG        = T(0);
					tS        = T(0);
					tScale    = T(0);

					if (i < iRows)
					{
						for (k = i; k < iRows; k++)
						{
							tScale += _mag(pUData[k * iCols + i]);
						}

						if (tScale != T(0))
						{
							for (k = i; k < iRows; k++)
							{
								iURP          = k * iCols + i;
								pUData[iURP] /= tScale;
								tS           += pUData[iURP] * pUData[iURP];
							}

							tF                = pUData[iURPi + i];
							tG                = -_sign(T(::sqrt(double(tS))), tF);
							tH                = tF * tG - tS;
							pUData[iURPi + i] = tF - tG;

							for (j = l; j < iCols; j++)
							{
								tS = T(0);
								for (k = i; k < iRows; k++)
								{
									iURP = k * iCols;
									tS  += pUData[iURP + i] * pUData[iURP + j];
								}

								tF = tS / tH;
								for (k = i; k < iRows; k++)
								{
									iURP              = k * iCols;
									pUData[iURP + j] += tF * pUData[iURP + i];
								}
							}	// for(j=l;j<cols;j++)

							for (k = i; k < iRows; k++)
							{
								pUData[k * iCols + i] *= tScale;
							}
						}	// if (scale != T(0))
					}	// if (i < rows)

					pWData[i] = tScale * tG;
					tG        = T(0);
					tS        = T(0);
					tScale    = T(0);

					if ((i < iRows) && (i != iCols))
					{
						for (k = l; k < iCols; k++)
						{
							tScale += _mag(pUData[iURPi + k]);
						}

						if (tScale != T(0))
						{
							for (k = l; k < iCols; k++)
							{
								iURP          = iURPi + k;
								pUData[iURP] /= tScale;
								tS           += pUData[iURP] * pUData[iURP];
							}

							tF                = pUData[iURPi + l];
							tG                = -_sign(T(::sqrt(double(tS))), tF);
							tH                = tF * tG - tS;
							pUData[iURPi + l] = tF - tG;

							for (k = l; k < iCols; k++)
							{
								vecRV1[k] = pUData[iURPi + k] / tH;
							}

							for (j = l; j < iRows; j++)
							{
								iURPj = j * iCols;

								tS = T(0);
								for (k = l; k < iCols; k++)
								{
									tS += pUData[iURPj + k] * pUData[iURPi + k];
								}

								for (k = l; k < iCols; k++)
								{
									pUData[iURPj + k] += tS * vecRV1[k];
								}
							}	// for(j=l;j<rows;j++)

							for (k = l; k < iCols; k++)
							{
								pUData[iURPi + k] *= tScale;
							}
						}	// if (scale != T(0))
					}	// if (i < rows && i != cols)

					tAnorm = _maxi(tAnorm, (_mag(pWData[i]) + _mag(vecRV1[i])));
				}	// for(i=0,l=1;i<cols;i++,l++)

				// Accumulation of right-hand transformations

				for (i = iCols - 1; i >= 0; i--)
				{
					l = i + 1;
					iURPi = i * iCols;

					if (i < iCols - 1)
					{
						if (tG != T(0))
						{
							for (j = l; j < iCols; j++)
							{
								pVData[j * iCols + i] = (pUData[iURPi + j] / pUData[iURPi + l]) / tG;
							}

							for (j = l; j < iCols; j++)
							{
								tS = T(0);
								for (k = l; k < iCols; k++)
								{
									tS += pUData[iURPi + k] * pVData[k * iCols + j];
								}

								for (k = l; k < iCols; k++)
								{
									iVRP              = k * iCols;
									pVData[iVRP + j] += tS * pVData[iVRP + i];
								}
							}	// for(j=l;j<cols;j++)
						}	// if (tG != T(0))

						for (j = l; j < iCols; j++)
						{
							pVData[iURPi + j]     = T(0);
							pVData[j * iCols + i] = T(0);
						}
					}	// if (i < cols-1)

					pVData[iURPi + i] = T(1);
					tG                = vecRV1[i];
				}	// for(i=cols-1,l=cols;l>0;i--,l--)

				// Accumulation of left-hand transformations

				if (iRows < iCols)
				{
					rcmin = iRows;
				}
				else
				{
					rcmin = iCols;
				}

				for (i = rcmin - 1; i >= 0; i--)
				{
					l = i + 1;
					iURPi = i * iCols;

					tG = pWData[i];

					for (j = l; j < iCols; j++)
					{
						pUData[iURPi + j] = T(0);
					}

					if (tG != T(0))
					{
						tG = T(1) / tG;

						for (j = l; j < iCols; j++)
						{
							tS = T(0);
							for (k = l; k < iRows; k++)
							{
								iURP = k * iCols;
								tS  += pUData[iURP + i] * pUData[iURP + j];
							}

							tF = (tS / pUData[iURPi + i]) * tG;

							for (k = i; k < iRows; k++)
							{
								iURP              = k * iCols;
								pUData[iURP + j] += tF * pUData[iURP + i];
							}
						}	// for(j=l;j<cols;j++)

						for (j = i; j < iRows; j++)
						{
							pUData[j * iCols + i] *= tG;
						}
					}	// if (tG != T(0))
					else
					{
						for (j = i; j < iRows; j++)
						{
							pUData[j * iCols + i] = T(0);
						}
					}

					pUData[iURPi + i] += T(1);
				}	// for(i=rcmin-1,l=rcmin;l>0;i--,l--)

				// Diagonalization of the bidiagonal form

				int status = 0;

				for (k = iCols - 1, hi = iCols; hi > 0; k--, hi--)	// Loop over singular values
				{
					for (iItCnt = 0; iItCnt < _MAXSVDITS_; iItCnt++)// Loop over allowed iteration
					{
						status = 0;

						for (l = k, iCR = int(k - 1), hj = k + 1; hj > 0; l--, iCR--, hj--)	// Test for splitting
						{
							if ((_mag(vecRV1[l]) + tAnorm) == tAnorm)
							{
								status = 1;
								break;
							}

							if (iCR >= 0)
							{
								if ((_mag(pWData[iCR]) + tAnorm) == tAnorm)
								{
									break;
								}
							}
						}	// Test for splitting

						if (!status)
						{
							tC = T(0);
							tS = T(1);

							for (i = l; i <= k; i++)
							{
								tF         = tS * vecRV1[i];
								vecRV1[i] *= tC;

								if ((_mag(tF) + tAnorm) == tAnorm)
								{
									break;
								}

								tG        = pWData[i];
								tH        = _EvalPythag(tF, tG);
								pWData[i] = tH;
								tH        = T(1) / tH;
								tC        = tG * tH;
								tS        = -(tF * tH);

								for (j = 0; j < iRows; j++)
								{
									iURPj = j * iCols;

									tY                  = pUData[iURPj + iCR];
									tZ                  = pUData[iURPj + i];
									pUData[iURPj + iCR] = (tY * tC) + (tZ * tS);
									pUData[iURPj + i]   = -(tY * tS) + (tZ * tC);
								}	// for(j=0;j<rows;j++)
							}	// for(i=l;i<=k;i++)
						}	// if (!status)

						tZ = pWData[k];
						if (l == k)			// Convergence
						{
							if (tZ < T(0))
							{
								pWData[k] = -tZ;
								for (j = 0; j < iCols; j++)
								{
									iVRP         = j * iCols + k;
									pVData[iVRP] = -pVData[iVRP];
								}
							}	// if (tZ < T(0))

							break;				// Exit
						}	// if (l == k)

						if (iItCnt == _MAXSVDITS_)
						{
							TAN_THROW_RT("exceeded maximum number of iterations");
						}

						tX  = pWData[l];
						iCR = k - 1;
						tY  = pWData[iCR];
						tG  = vecRV1[iCR];
						tH  = vecRV1[k];

						tF = ((tY - tZ) * (tY + tZ) + (tG - tH) * (tG + tH)) / (T(2) * tH * tY);
						tG = _EvalPythag(tF, T(1));
						tF = ((tX - tZ) * (tX + tZ) + tH * ((tY / (tF + _sign(tG, tF))) - tH)) / tX;

						// Next QR transformation

						tC = T(1);
						tS = T(1);
						for (j = l, i = l + 1; j <= iCR; j++, i++)
						{
							tG        = vecRV1[i];
							tY        = pWData[i];
							tH        = tS * tG;
							tG       *= tC;
							tZ        = _EvalPythag(tF, tH);
							vecRV1[j] = tZ;

							tC  = tF / tZ;
							tS  = tH / tZ;
							tF  = (tX * tC) + (tG * tS);
							tG  = -(tX * tS) + (tG * tC);
							tH  = tY * tS;
							tY *= tC;

							for (jj = 0; jj < iCols; jj++)
							{
								iVRP             = jj * iCols;
								tX               = pVData[iVRP + j];
								tZ               = pVData[iVRP + i];
								pVData[iVRP + j] = (tX * tC) + (tZ * tS);
								pVData[iVRP + i] = -(tX * tS) + (tZ * tC);
							}

							tZ        = _EvalPythag(tF, tH);
							pWData[j] = tZ;

							if (tZ != T(0))
							{
								tZ = T(1) / tZ;
								tC = tF * tZ;
								tS = tH * tZ;
							}

							tF = (tC * tG) + (tS * tY);
							tX = -(tS * tG) + (tC * tY);

							for (jj = 0; jj < iRows; jj++)
							{
								iURP             = jj * iCols;
								tY               = pUData[iURP + j];
								tZ               = pUData[iURP + i];
								pUData[iURP + j] = (tY * tC) + (tZ * tS);
								pUData[iURP + i] = -(tY * tS) + (tZ * tC);
							}
						}	// for(j=l,i=l+1;j<cr;j++,i++)

						vecRV1[l] = T(0);
						vecRV1[k] = tF;
						pWData[k] = tX;
					}	// for(its=0;its<_MAXSVDITS_;its++)
				}	// for(k=cols-1;k>=0;k--)     // Loop over singular values
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error calculating SVD", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Order mW in decending or ascending order and adjust COLS of mV and mU.
		/// </summary>
		///
		/// <param name="matU">		   [in,out] The matrix u. </param>
		/// <param name="matD">		   [in,out] The matrix d. </param>
		/// <param name="matV">		   [in,out] The matrix v. </param>
		/// <param name="bDescending"> (Optional) true to descending. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		static void Order(CMatrix<T>& matU, CMatrix<T>& matD, CMatrix<T>& matV, bool bDescending = true)
		{
			// Ensure that a possible transposition of matU, matD, matV is represented in memory,
			// since we are not working with iterators here.
			matU.ApplyToMemory();
			matD.ApplyToMemory();
			matV.ApplyToMemory();

			int k, j, i, iColCnt;
			T tValue;

			iColCnt = int(matD.GetColCount());

			if (iColCnt <= 0)
			{
				TAN_THROW_RT("Empty diagonal matrix");
			}

			T* ptW = matD.GetDataPtr();

			for (i = 0; i < iColCnt - 1; i++)
			{
				k      = i;
				tValue = ptW[i];
				for (j = i + 1; j < iColCnt; j++)
				{
					if (((_mag(ptW[j]) >= _mag(tValue)) && bDescending) || ((_mag(ptW[j]) <= _mag(tValue)) && !bDescending))
					{
						k      = j;
						tValue = ptW[j];
					}
				}

				if (k != i)
				{
					ptW[k] = ptW[i];
					ptW[i] = tValue;
					matV.SwapCols(i, k);
					matU.SwapCols(i, k);
				}
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Inverse of this matrix using SVD.
		/// </summary>
		///
		/// <param name="mA">    The matrix. </param>
		/// <param name="tPrec"> The precision. </param>
		///
		/// <returns> The inverse matrix. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		static CMatrix<T> Inverse(const CMatrix<T>& matA, T tPrec)
		{
			try
			{
				int iRows = int(matA.GetRowCount());
				int iCols = int(matA.GetColCount());

				if ((iRows <= 0) || (iCols <= 0))
				{
					TAN_THROW_RT("Invalid matrix");
				}

				CMatrix<T> matInv(iRows, iCols);
				CMatrix<T> matU, matV, matW;

				SVD(matU, matW, matV, matA);

				matW.TinyToZero(tPrec);
				matW.CompInvert(T(0), tPrec);
				matW.VectorToDiagonal();

				matInv = matV * matW * matU.Transpose();

				return matInv;
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error calculating inverse SVD", xEx);
			}
		}


	protected:

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Magnitudes the given t value.
		/// </summary>
		///
		/// <param name="tValue"> The value. </param>
		///
		/// <returns> . </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		static T _mag(T tValue)
		{
			return tValue < T(0) ? -tValue : tValue;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Signs.
		/// </summary>
		///
		/// <param name="tA"> The t a. </param>
		/// <param name="tB"> The t b. </param>
		///
		/// <returns> . </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		static T _sign(T tA, T tB)
		{
			return tB >= T(0) ? _mag(tA) : -_mag(tA);
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Maxis.
		/// </summary>
		///
		/// <param name="tA"> The t a. </param>
		/// <param name="tB"> The t b. </param>
		///
		/// <returns> . </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		static T _maxi(T tA, T tB)
		{
			return tA >= tB ? tA : tB;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Calculate sqrt(a^2 + b^2) without destructive over- or underflow.
		/// </summary>
		///
		/// <param name="tA"> The t a. </param>
		/// <param name="tB"> The t b. </param>
		///
		/// <returns> . </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		static T _EvalPythag(T tA, T tB)
		{
			T at, bt, tH;

			at = _mag(tA);
			bt = _mag(tB);

			if (at > bt)
			{
				tH = bt / at;
				return at * T(::sqrt(double(T(1) + tH * tH)));
			}
			else if (bt == T(0))
			{
				return T(0);
			}
			else
			{
				tH = at / bt;
				return bt * T(::sqrt(double(T(1) + tH * tH)));
			}
		}
	};
}
