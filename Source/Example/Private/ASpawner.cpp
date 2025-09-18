// Source/Example/Private/ASpawner.cpp
#include "ASpawner.h"
#include "TimerManager.h"
#include "Engine/World.h"
#include "Math/UnrealMathUtility.h"
#include "Math/RotationMatrix.h"
#include "Kismet/KismetSystemLibrary.h"

ASpawner::ASpawner()
{
    PrimaryActorTick.bCanEverTick = false;
}

void ASpawner::BeginPlay()
{
    Super::BeginPlay();

    if (!SpawnClass)
    {
        UE_LOG(LogTemp, Warning, TEXT("Spawner: No SpawnClass set! Spawning will not work."));
        return;
    }

    if (!bMultipleSpawn)
    {
        SpawnObject();
    }
    else if (SpawnInterval > 0.0f && MaxSpawnCount > 0)
    {
        GetWorldTimerManager().SetTimer(SpawnTimerHandle, this, &ASpawner::SpawnObject, SpawnInterval, true);
        UE_LOG(LogTemp, Log, TEXT("Spawner: Started multiple spawn timer. Interval: %f, Max: %d"), SpawnInterval, MaxSpawnCount);
    }
}

void ASpawner::SpawnObject()
{
    CleanUpDestroyedActors();

    if (bMultipleSpawn && SpawnedActors.Num() >= MaxSpawnCount)
    {
        GetWorldTimerManager().ClearTimer(SpawnTimerHandle);
        UE_LOG(LogTemp, Log, TEXT("Spawner: Max spawn count (%d) reached. Stopping timer."), MaxSpawnCount);
        return;
    }

    FActorSpawnParameters SpawnParams;
    SpawnParams.Owner = this;
    SpawnParams.Instigator = GetInstigator();
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::DontSpawnIfColliding;

    AActor* NewActor = nullptr;
    const int32 MaxAttempts = 50;

    for (int32 Attempt = 0; Attempt < MaxAttempts; ++Attempt)
    {
        const FVector2D RandPoint = FMath::RandPointInCircle(SpawnRadius);
        const FVector TraceStart = GetActorLocation() + FVector(RandPoint.X, RandPoint.Y, TraceHeightAbove);
        const FVector TraceEnd = TraceStart + FVector(0.0f, 0.0f, -TraceHeightAbove * 2.0f);

        FHitResult HitResult;
        UKismetSystemLibrary::LineTraceSingle(
            this,
            TraceStart, TraceEnd,
            UEngineTypes::ConvertToTraceType(ECC_Visibility),
            false, TArray<AActor*>(),
            EDrawDebugTrace::None,
            HitResult,
            true
        );

        if (HitResult.bBlockingHit)
        {
            FVector SpawnLocation = HitResult.Location + FVector(0.0f, 0.0f, 1.0f);
            FRotator SpawnRotation = GetActorRotation();

            if (bAlignToSurface)
            {
                const FVector UpVector = HitResult.ImpactNormal.GetSafeNormal();
                SpawnRotation = FRotationMatrix::MakeFromZX(UpVector, GetActorForwardVector()).Rotator();
            }

            NewActor = GetWorld()->SpawnActor<AActor>(SpawnClass, SpawnLocation, SpawnRotation, SpawnParams);
            if (NewActor)
            {
                break;
            }
        }
    }

    if (NewActor)
    {
        SpawnedActors.Add(NewActor);
        NewActor->OnDestroyed.AddDynamic(this, &ASpawner::OnSpawnedActorDestroyed);
        UE_LOG(LogTemp, Log, TEXT("Spawner: Spawned. Current count: %d"), SpawnedActors.Num());
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("Spawner: Failed to find free surface location after %d attempts!"), MaxAttempts);
    }
}

void ASpawner::OnSpawnedActorDestroyed(AActor* /*DestroyedActor*/)
{
    CleanUpDestroyedActors();
}

void ASpawner::CleanUpDestroyedActors()
{
    SpawnedActors.RemoveAll([](const TWeakObjectPtr<AActor>& ActorPtr)
        {
            return !ActorPtr.IsValid();
        });
}
