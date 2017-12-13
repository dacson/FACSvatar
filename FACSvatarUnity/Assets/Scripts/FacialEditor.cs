using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class FacialEditor : MonoBehaviour {

    int blendShapeCount;
    SkinnedMeshRenderer skinnedMeshRenderer;
    Mesh skinnedMesh;
    int blendShapeNo1 = 0;
    int blendShapeNo2 = 0;
    int blendShapeNo3 = 0;
    int blendShapeNo4 = 0;
    int blendShapeNo5 = 0;
    int blendShapeNo6 = 0;
    //int blendShapeNo7 = 0;
    float blendVal = 0f;
    float blendSpeed = 2f;
    int reverser = 1;

    void Awake()
    {
        skinnedMeshRenderer = GetComponent<SkinnedMeshRenderer>();
        skinnedMesh = GetComponent<SkinnedMeshRenderer>().sharedMesh;
    }

    void Start()
    {
        blendShapeCount = skinnedMesh.blendShapeCount;
        // AU01
        blendShapeNo1 = skinnedMesh.GetBlendShapeIndex("Expressions_browsMidVert_max");
        // AU15
        blendShapeNo2 = skinnedMesh.GetBlendShapeIndex("Expressions_mouthSmile_min");
        // AU04
        blendShapeNo3 = skinnedMesh.GetBlendShapeIndex("Expressions_browOutVertL_min");
        blendShapeNo4 = skinnedMesh.GetBlendShapeIndex("Expressions_browOutVertR_min");
        blendShapeNo5 = skinnedMesh.GetBlendShapeIndex("Expressions_browSqueezeL_max");
        blendShapeNo6 = skinnedMesh.GetBlendShapeIndex("Expressions_browSqueezeR_max");
        //blendShapeNo7 = skinnedMesh.GetBlendShapeIndex("Expressions_browsMidVert_min");
    }

    void Update()
    {
        skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo1, blendVal * .7f);
        skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo2, blendVal);
        skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo3, blendVal * .4f);
        skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo4, blendVal * .4f);
        skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo5, blendVal);
        skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo6, blendVal);
        //skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo7, blendVal);

        blendVal += blendSpeed * reverser;
        if (blendVal >= 100 || blendVal < 0)
        {
            // Switch between going to neutral or expression
            reverser *= -1;
        }

        //skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo3, blendVal);
        //if (blendShapeNo < blendShapeCount)
        //{
        //    Debug.Log(blendShapeNo);
        //    if (blendVal < 100f)
        //    {
        //        skinnedMeshRenderer.SetBlendShapeWeight(blendShapeNo, blendVal);
        //        blendVal += blendSpeed;
        //    }

        //    else
        //    {
        //        blendVal = 0f;
        //        blendShapeNo += 1;
        //    }
        //}
    }
}
